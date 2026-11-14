from fastapi import APIRouter, status
from app.views.schemas import ExtraerRequest, ExtraerResponse
from app.services.etl_service import extraer_y_guardar_obras

router = APIRouter(prefix="/etl", tags=["ETL Pipeline"])

@router.post(
    "/extraer",
    response_model=ExtraerResponse,
    status_code=status.HTTP_201_CREATED
)
def extraer_datos(request: ExtraerRequest):
    return extraer_y_guardar_obras(request.cantidad)
