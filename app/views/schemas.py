from typing import Any, Dict, List, Optional, Union
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

class ColumnaCategoricaResponse(BaseModel):
    columna: str
    tipo: str
    valores_unicos: int
    distribucion: Dict[str, int]
    valor_mas_comun: Optional[str] = None
    nulos: int

class ColumnaNumericaResponse(BaseModel):
    columna: str
    tipo: str
    min: Optional[float] = None
    max: Optional[float] = None
    promedio: Optional[float] = None
    mediana: Optional[float] = None
    desviacion_std: Optional[float] = None
    nulos: int

class ColumnaFechaResponse(BaseModel):
    columna: str
    tipo: str
    min: Optional[str] = None
    max: Optional[str] = None
    rango_dias: int
    nulos: int

class ColumnaBooleanaResponse(BaseModel):
    columna: str
    tipo: str
    true: int
    false: int
    nulos: int

class ColumnaTextoResponse(BaseModel):
    columna: str
    tipo: str
    valores_unicos: int
    nulos: int

AnaliticaColumnaResponse = Union[
    ColumnaCategoricaResponse,
    ColumnaNumericaResponse,
    ColumnaFechaResponse,
    ColumnaBooleanaResponse,
    ColumnaTextoResponse,
]