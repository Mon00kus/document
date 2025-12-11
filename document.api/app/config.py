"""
Configuración de la aplicación usando variables de entorno.
Para Docker, estas variables se pueden pasar a través de docker-compose.yml
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Database
    DATABASE_URL: str = "mssql+aioodbc://sa:documentPassword123!@localhost:1433/documentdb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    
    # JWT
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AWS S3 / MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "documents"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: str = "false"
    
    @property
    def s3_use_ssl_bool(self) -> bool:
        """Convierte S3_USE_SSL a booleano"""
        return self.S3_USE_SSL.lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:8081",
        "http://localhost:3000",
        "https://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5002",
        "https://localhost:5002",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

