from typing import Any, Dict, List, Optional
import pandas as pd
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import artworks_collection
from app.models.entidad_sql import ArtworkMaster

def _sanitizar_documento_mongo(documento: Dict[str, Any]) -> Dict[str, Any]:
    limpio: Dict[str, Any] = {}
    for clave, valor in documento.items():
        if isinstance(valor, ObjectId):
            limpio[clave] = str(valor)
        else:
            limpio[clave] = valor
    return limpio

def _serializar_registro_sql(registro: ArtworkMaster) -> Dict[str, Any]:
    return {
        "id": registro.id,
        "titulo": registro.titulo,
        "artista": registro.artista,
        "departamento": registro.departamento,
        "clasificacion": registro.clasificacion,
        "origen": registro.origen,
        "anio_inicio": registro.anio_inicio,
        "anio_fin": registro.anio_fin,
        "es_dominio_publico": registro.es_dominio_publico,
        "fecha_actualizacion_api": (
            registro.fecha_actualizacion_api.isoformat()
            if registro.fecha_actualizacion_api is not None
            else None
        ),
        "total_categorias": registro.total_categorias,
    }

def obtener_perfil_dual(obra_id: int, db: Session) -> Dict[str, Any]:
    try:
        doc_mongo = artworks_collection.find_one({"_id": obra_id})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar MongoDB: {str(exc)}"
        )

    try:
        registro_sql = (
            db.query(ArtworkMaster)
            .filter(ArtworkMaster.id == obra_id)
            .first()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar MySQL: {str(exc)}"
        )

    if doc_mongo is None and registro_sql is None:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún registro con id={obra_id} en MongoDB ni en MySQL."
        )

    vista_mongo: Optional[Dict[str, Any]] = (
        _sanitizar_documento_mongo(doc_mongo) if doc_mongo is not None else None
    )
    vista_sql: Optional[Dict[str, Any]] = (
        _serializar_registro_sql(registro_sql) if registro_sql is not None else None
    )

    warning: Optional[str] = None
    if vista_mongo is not None and vista_sql is None:
        warning = (
            "Registro existe en MongoDB pero no en MySQL. "
            "Posiblemente no se ha ejecutado /transformar o el registro falló en la transformación."
        )
    elif vista_mongo is None and vista_sql is not None:
        warning = (
            "Registro existe en MySQL pero no en MongoDB. "
            "Posible inconsistencia o eliminación parcial en la capa de staging."
        )

    return {
        "id": obra_id,
        "vista_mongo": vista_mongo,
        "vista_sql": vista_sql,
        "warning": warning,
    }

def _detectar_tipo_columna(columna_sql: Any, serie_valida: pd.Series) -> str:
    tipo_sql = columna_sql.type

    # 1. Booleana (BOOLEAN explícito en SQLAlchemy o TINYINT(1) con valores 0 y 1)
    if isinstance(tipo_sql, Boolean):
        return "booleana"

    if isinstance(tipo_sql, (Integer, Float, Numeric)):
        if len(serie_valida) > 0 and set(serie_valida.tolist()).issubset({0, 1, True, False}):
            return "booleana"
        return "numerica"

    # 2. Fecha (DATE o DATETIME)
    if isinstance(tipo_sql, (Date, DateTime)):
        return "fecha"

    # 3. Texto: categórica (valores repetidos) vs texto libre (todos distintos)
    textos = serie_valida.astype(str)
    if len(textos) == 0 or textos.nunique() == len(textos):
        return "texto"
    return "categorica"


def _detectar_tipo_columna(columna_sql: Any, serie_valida: pd.Series) -> str:
    tipo_sql = columna_sql.type

    # 1. Booleana (BOOLEAN explícito en SQLAlchemy o TINYINT(1) con valores 0 y 1)
    if isinstance(tipo_sql, Boolean):
        return "booleana"

    if isinstance(tipo_sql, (Integer, Float, Numeric)):
        if len(serie_valida) > 0 and set(serie_valida.tolist()).issubset({0, 1, True, False}):
            return "booleana"
        return "numerica"

    # 2. Fecha (DATE o DATETIME)
    if isinstance(tipo_sql, (Date, DateTime)):
        return "fecha"

    # 3. Texto: categórica (valores repetidos) vs texto libre (todos distintos)
    textos = serie_valida.astype(str)
    if len(textos) == 0 or textos.nunique() == len(textos):
        return "texto"
    return "categorica"


def _detectar_tipo_columna(columna_sql: Any, serie_valida: pd.Series) -> str:
    tipo_sql = columna_sql.type

    # 1. Booleana (BOOLEAN explícito en SQLAlchemy o TINYINT(1) con valores 0 y 1)
    if isinstance(tipo_sql, Boolean):
        return "booleana"

    if isinstance(tipo_sql, (Integer, Float, Numeric)):
        if len(serie_valida) > 0 and set(serie_valida.tolist()).issubset({0, 1, True, False}):
            return "booleana"
        return "numerica"

    # 2. Fecha (DATE o DATETIME)
    if isinstance(tipo_sql, (Date, DateTime)):
        return "fecha"

    # 3. Texto: categórica (valores repetidos) vs texto libre (todos distintos)
    textos = serie_valida.astype(str)
    if len(textos) == 0 or textos.nunique() == len(textos):
        return "texto"
    return "categorica"


def _analizar_numerica(nombre: str, serie_valida: pd.Series, nulos: int) -> Dict[str, Any]:
    valores_num = pd.to_numeric(serie_valida, errors="coerce").dropna()

    if len(valores_num) == 0:
        return {
            "columna": nombre,
            "tipo": "numerica",
            "min": None,
            "max": None,
            "promedio": None,
            "mediana": None,
            "desviacion_std": None,
            "nulos": nulos,
        }

    desviacion = round(float(valores_num.std()), 2) if len(valores_num) > 1 else 0.0

    return {
        "columna": nombre,
        "tipo": "numerica",
        "min": round(float(valores_num.min()), 2),
        "max": round(float(valores_num.max()), 2),
        "promedio": round(float(valores_num.mean()), 2),
        "mediana": round(float(valores_num.median()), 2),
        "desviacion_std": desviacion,
        "nulos": nulos,
    }


def _analizar_booleana(nombre: str, serie_valida: pd.Series, nulos: int) -> Dict[str, Any]:
    valores_bool = serie_valida.map(lambda x: bool(x))
    conteo_true = int(valores_bool.sum())
    conteo_false = int((~valores_bool).sum())

    return {
        "columna": nombre,
        "tipo": "booleana",
        "true": conteo_true,
        "false": conteo_false,
        "nulos": nulos,
    }


def _analizar_fecha(nombre: str, serie_valida: pd.Series, nulos: int) -> Dict[str, Any]:
    fechas = pd.to_datetime(serie_valida, errors="coerce").dropna()

    if len(fechas) == 0:
        return {
            "columna": nombre,
            "tipo": "fecha",
            "min": None,
            "max": None,
            "rango_dias": 0,
            "nulos": nulos,
        }

    fecha_min = fechas.min()
    fecha_max = fechas.max()
    rango_dias = int((fecha_max - fecha_min).days)

    return {
        "columna": nombre,
        "tipo": "fecha",
        "min": fecha_min.strftime("%Y-%m-%d"),
        "max": fecha_max.strftime("%Y-%m-%d"),
        "rango_dias": rango_dias,
        "nulos": nulos,
    }


def _analizar_categorica(nombre: str, serie_valida: pd.Series, nulos: int) -> Dict[str, Any]:
    textos = serie_valida.astype(str)
    conteos = textos.value_counts()
    distribucion = {str(categoria): int(cantidad) for categoria, cantidad in conteos.items()}
    valor_mas_comun = str(conteos.index[0]) if len(conteos) > 0 else None

    return {
        "columna": nombre,
        "tipo": "categorica",
        "valores_unicos": int(textos.nunique()),
        "distribucion": distribucion,
        "valor_mas_comun": valor_mas_comun,
        "nulos": nulos,
    }


def _analizar_texto(nombre: str, serie_valida: pd.Series, nulos: int) -> Dict[str, Any]:
    return {
        "columna": nombre,
        "tipo": "texto",
        "valores_unicos": int(serie_valida.astype(str).nunique()),
        "nulos": nulos,
    }


def analizar_columna(nombre: str, db: Session) -> Dict[str, Any]:
    nombre = nombre.strip()
    columnas_tabla = ArtworkMaster.__table__.columns
    columnas_validas: List[str] = list(columnas_tabla.keys())

    if nombre not in columnas_validas:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": f"La columna '{nombre}' no existe en la tabla '{ArtworkMaster.__tablename__}'.",
                "columnas_validas": columnas_validas,
            },
        )

    columna_sql = columnas_tabla[nombre]

    try:
        filas = db.query(getattr(ArtworkMaster, nombre)).all()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar la columna '{nombre}' en MySQL: {str(exc)}",
        )

    serie = pd.Series([fila[0] for fila in filas], dtype="object")
    nulos = int(serie.isna().sum())
    serie_valida = serie.dropna()
    tipo_detectado = _detectar_tipo_columna(columna_sql, serie_valida)

    if tipo_detectado == "numerica":
        return _analizar_numerica(nombre, serie_valida, nulos)

    if tipo_detectado == "booleana":
        return _analizar_booleana(nombre, serie_valida, nulos)

    if tipo_detectado == "fecha":
        return _analizar_fecha(nombre, serie_valida, nulos)

    if tipo_detectado == "categorica":
        return _analizar_categorica(nombre, serie_valida, nulos)

    return _analizar_texto(nombre, serie_valida, nulos)