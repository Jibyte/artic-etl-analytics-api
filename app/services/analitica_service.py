from typing import Any, Dict, Optional
from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError
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
