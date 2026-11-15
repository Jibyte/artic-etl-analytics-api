from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from app.views.schemas import (
    ExtraerRequest,
    ExtraerResponse,
    TransformarResponse,
    ResetResponse,
)
from app.services.etl_service import (
    extraer_y_guardar_obras,
    transformar_y_cargar_obras,
    reset_pipeline,
)
from app.database import get_db

router = APIRouter(prefix="/etl", tags=["ETL Pipeline"])


@router.post(
    "/extraer",
    response_model=ExtraerResponse,
    status_code=status.HTTP_201_CREATED
)
def extraer_datos(request: ExtraerRequest):
    return extraer_y_guardar_obras(request.cantidad)


@router.post(
    "/transformar",
    response_model=TransformarResponse,
    status_code=status.HTTP_200_OK
)
def transformar_datos(db: Session = Depends(get_db)):
    return transformar_y_cargar_obras(db)



