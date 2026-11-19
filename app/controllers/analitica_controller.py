from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.views.schemas import PerfilDualResponse, AnaliticaColumnaResponse
from app.services.analitica_service import obtener_perfil_dual, analizar_columna

router = APIRouter(prefix="/analitica", tags=["Analítica"])

@router.get(
    "/perfil/{id}",
    response_model=PerfilDualResponse
)
def consultar_perfil_dual(id: int, db: Session = Depends(get_db)):
    return obtener_perfil_dual(id, db)

@router.get(
    "/columna/{nombre}",
    response_model=AnaliticaColumnaResponse
)
def consultar_analitica_columna(nombre: str, db: Session = Depends(get_db)):
    return analizar_columna(nombre, db)