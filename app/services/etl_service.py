from typing import Any, Dict, List
import requests
import pandas as pd
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from app.config import settings
from app.database import artworks_collection
from sqlalchemy.exc import SQLAlchemyError
from app.models.entidad_sql import ArtworkMaster
from sqlalchemy import text
from sqlalchemy.dialects.mysql import insert

def obtener_obras_api(cantidad: int) -> List[Dict[str, Any]]:
    obras_recolectadas: List[Dict[str, Any]] = []
    pagina_actual = 1
    headers = {
        "User-Agent": "artic-etl-analytics-api/1.0 (Academic Data Engineering Project)"
    }

    while len(obras_recolectadas) < cantidad:
        restantes = cantidad - len(obras_recolectadas)
        limite_pagina = min(100, restantes)

        try:
            respuesta = requests.get(
                settings.API_BASE_URL,
                params={"page": pagina_actual, "limit": limite_pagina},
                headers=headers,
                timeout=15
            )
            respuesta.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Error al consultar la API externa del Art Institute of Chicago: {str(exc)}"
            )

        payload = respuesta.json()
        datos_pagina = payload.get("data", [])

        if not datos_pagina:
            break

        obras_recolectadas.extend(datos_pagina)

        paginacion = payload.get("pagination", {})
        total_paginas = paginacion.get("total_pages", pagina_actual)
        if pagina_actual >= total_paginas:
            break

        pagina_actual += 1

    return obras_recolectadas[:cantidad]

def extraer_y_guardar_obras(cantidad: int) -> Dict[str, Any]:
    obras = obtener_obras_api(cantidad)
    nuevos = 0
    ya_existentes = 0

    try:
        for obra in obras:
            obra_id = obra.get("id")
            if obra_id is None:
                continue

            documento = dict(obra)
            documento["_id"] = int(obra_id)

            resultado = artworks_collection.update_one(
                {"_id": documento["_id"]},
                {"$set": documento},
                upsert=True
            )

            if resultado.upserted_id is not None:
                nuevos += 1
            else:
                ya_existentes += 1
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al persistir documentos en MongoDB: {str(exc)}"
        )

    return {
        "mensaje": "Datos extraídos exitosamente",
        "nuevos": nuevos,
        "ya_existentes": ya_existentes,
        "fuente": settings.API_SOURCE_NAME,
        "status": 201
    }

def transformar_y_cargar_obras(db):
    try:
        documentos = list(artworks_collection.find({}))

        if not documentos:
            return {
                "mensaje": "No hay documentos para transformar",
                "registros_procesados": 0,
                "tabla_destino": "artworks_master",
                "status": 200
            }

        # Aplanamos los documentos de MongoDB con Pandas.
        df = pd.json_normalize(documentos, sep="_")

        registros = []
        ids_procesados = set()

        for _, fila in df.iterrows():
            categorias = fila.get("category_titles", [])

            if not isinstance(categorias, list):
                categorias = []

            fecha = pd.to_datetime(
                fila.get("source_updated_at"),
                errors="coerce",
                utc=True
            )

            fecha_actualizacion = (
                fecha.date() if pd.notna(fecha) else None
            )

            def texto(columna):
                valor = fila.get(columna)

                if valor is None or not isinstance(valor, (str, int, float, bool)):
                     return "N/A"

                if pd.isna(valor) or not str(valor).strip():
                     return "N/A"

                return str(valor)
            
            def numero(columna):
                valor = pd.to_numeric(
                    fila.get(columna), errors="coerce"
                )
                return int(valor) if pd.notna(valor) else None

            # Validamos que la obra tenga un identificador numérico válido
            try:
                obra_id = int(fila["_id"])

                if obra_id <= 0:
                    continue

            except (ValueError, TypeError, KeyError):
                continue

            # Evitamos procesar obras con identificadores repetidos
            if obra_id in ids_procesados:
                continue

            ids_procesados.add(obra_id)

            registros.append(
                ArtworkMaster(
                    id=obra_id,
                    titulo=texto("title"),
                    artista=texto("artist_display"),
                    departamento=texto("department_title"),
                    clasificacion=texto("classification_title"),
                    origen=texto("place_of_origin"),
                    anio_inicio=numero("date_start"),
                    anio_fin=numero("date_end"),
                    es_dominio_publico=(
                        bool(fila["is_public_domain"])
                        if pd.notna(fila.get("is_public_domain"))
                        else None
                    ),
                    fecha_actualizacion_api=fecha_actualizacion,
                    total_categorias=len(categorias)
                )
            )

         # Convertimos los registros del modelo en diccionarios
        datos = [
            {
                columna.name: getattr(registro, columna.name)
                for columna in ArtworkMaster.__table__.columns
            }
            for registro in registros
        ]

        # Identificamos cuáles registros todavía no existen
        ids_existentes = {
            resultado[0]
            for resultado in db.query(ArtworkMaster.id).all()
        }

        registros_nuevos = sum(
            1 for registro in registros
            if registro.id not in ids_existentes
        )

        # Insertamos las obras nuevas y actualizamos las existentes
        if datos:
            consulta = insert(ArtworkMaster).values(datos)

            columnas_actualizables = {
                columna.name: consulta.inserted[columna.name]
                for columna in ArtworkMaster.__table__.columns
                if columna.name != "id"
            }

            consulta = consulta.on_duplicate_key_update(
                **columnas_actualizables
            )

            db.execute(consulta)
            db.commit()

        return {
            "mensaje": "Pipeline finalizado",
            "registros_procesados": registros_nuevos,
            "tabla_destino": "artworks_master",
            "status": 200
        }

    except (PyMongoError, SQLAlchemyError, ValueError, TypeError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error en la transformación y carga: {str(exc)}"
        )

def reset_pipeline(db):
    try:
        # Contamos las filas de MySQL antes de vaciar la tabla
        total_mysql = db.query(ArtworkMaster).count()

        # Vaciamos MySQL conservando la tabla y su clave primaria
        db.execute(text("TRUNCATE TABLE artworks_master"))

        # Eliminamos todos los documentos de MongoDB
        resultado_mongo = artworks_collection.delete_many({})

        return {
            "mensaje": "Sistema reseteado correctamente",
            "mongo_docs_eliminados": resultado_mongo.deleted_count,
            "mysql_rows_eliminadas": total_mysql,
            "status": 200
        }

    except (PyMongoError, SQLAlchemyError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al resetear el pipeline: {str(exc)}"
        )