from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app.models import entidad_sql
from app.controllers import etl_controller, analitica_controller

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Art Institute of Chicago - ETL & Analytics API",
    description="Pipeline ETL idempotente hacia MongoDB y MySQL con analítica dinámica y auditoría dual.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(etl_controller.router, prefix="/api/v1")
app.include_router(analitica_controller.router, prefix="/api/v1")

@app.get("/", tags=["Healthcheck"])
def root():
    return {
        "servicio": "artic-etl-analytics-api",
        "estado": "activo",
        "documentacion": "/docs"
    }
