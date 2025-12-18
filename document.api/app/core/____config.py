from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # AWS / S3
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"
    AWS_ENDPOINT_URL: str = "http://localhost:4566"  # LocalStack
    S3_BUCKET_NAME: str = "documents-bucket"
    S3_USE_SSL: str = "false"

    @property
    def s3_use_ssl_bool(self) -> bool:
        """Convierte S3_USE_SSL a booleano"""
        return self.S3_USE_SSL.lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://localhost:3000",
        "https://localhost:5173",
        "http://localhost:5002",
        "https://localhost:5002",
    ]

    class Config:
        env_file = ".env.dev"
        case_sensitive = True

settings = Settings()