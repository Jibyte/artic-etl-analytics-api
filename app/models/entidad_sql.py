from sqlalchemy import Column, Integer, String, Date, Boolean
from app.database import Base

class ArtworkMaster(Base):
    __tablename__ = "artworks_master"

    id = Column(Integer, primary_key=True, autoincrement=False, index=True)
    titulo = Column(String(255), nullable=False)
    artista = Column(String(255), nullable=True)
    departamento = Column(String(150), nullable=True)
    clasificacion = Column(String(150), nullable=True)
    origen = Column(String(150), nullable=True)
    anio_inicio = Column(Integer, nullable=True)
    anio_fin = Column(Integer, nullable=True)
    es_dominio_publico = Column(Boolean, nullable=True)
    fecha_actualizacion_api = Column(Date, nullable=True)
    total_categorias = Column(Integer, nullable=True)
