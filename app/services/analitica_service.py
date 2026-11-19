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


def analizar_columna(nombre: str, db: Session) -> Dict[str, Any]:
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

    return {
        "columna": nombre,
        "tipo": tipo_detectado,
        "valores_unicos": int(serie_valida.nunique()),
        "nulos": nulos,
    }