from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.views.schemas import PerfilDualResponse
from app.services.analitica_service import obtener_perfil_dual

router = APIRouter(prefix="/analitica", tags=["Analítica"])

@router.get(
    "/perfil/{id}",
    response_model=PerfilDualResponse
)
def consultar_perfil_dual(id: int, db: Session = Depends(get_db)):
    return obtener_perfil_dual(id, db)
