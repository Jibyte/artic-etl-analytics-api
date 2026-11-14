from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ExtraerRequest(BaseModel):
    cantidad: int = Field(..., gt=0, description="Cantidad de obras a extraer desde la API")

class ExtraerResponse(BaseModel):
    mensaje: str
    nuevos: int
    ya_existentes: int
    fuente: str
    status: int

class TransformarResponse(BaseModel):
    mensaje: str
    registros_procesados: int
    tabla_destino: str
    status: int

class ResetResponse(BaseModel):
    mensaje: str
    mongo_docs_eliminados: int
    mysql_rows_eliminadas: int
    status: int

class PerfilDualResponse(BaseModel):
    id: int
    vista_mongo: Optional[Dict[str, Any]] = None
    vista_sql: Optional[Dict[str, Any]] = None
    warning: Optional[str] = None
