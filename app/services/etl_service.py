from typing import Any, Dict, List
import requests
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from app.config import settings
from app.database import artworks_collection

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
