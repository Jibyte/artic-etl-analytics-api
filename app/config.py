import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.artic.edu/api/v1/artworks")
    API_SOURCE_NAME: str = os.getenv("API_SOURCE_NAME", "Art Institute of Chicago API")

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "artic_staging")
    MONGO_COLLECTION_NAME: str = os.getenv("MONGO_COLLECTION_NAME", "artworks_raw")

    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB_NAME: str = os.getenv("MYSQL_DB_NAME", "artic_dw")

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+mysqlconnector://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB_NAME}"
        )

settings = Settings()
