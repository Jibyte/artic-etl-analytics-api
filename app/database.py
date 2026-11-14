from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
mongo_db = mongo_client[settings.MONGO_DB_NAME]
artworks_collection = mongo_db[settings.MONGO_COLLECTION_NAME]

def ensure_mysql_database() -> None:
    server_url = (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}"
    )
    temp_engine = create_engine(server_url)
    with temp_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()
    temp_engine.dispose()

ensure_mysql_database()

engine = create_engine(settings.mysql_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
