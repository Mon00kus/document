import logging
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
from app.config import settings  # Ajusta si tu estructura cambió
from botocore.exceptions import ClientError

logger = logging.getLogger("s3_utils")  # o el nombre del módulo

def get_s3_client():
    """
    Crea un cliente S3 compatible con LocalStack si settings.AWS_ENDPOINT_URL está definido.
    """
    kwargs = {
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        # útil para LocalStack
        "config": Config(s3={"addressing_style": "path"}),
    }
    if getattr(settings, "AWS_ENDPOINT_URL", None):
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("s3", **kwargs)

def download_file_from_s3(s3_key: str, bucket: Optional[str] = None) -> bytes:
    bucket_name = bucket or settings.S3_BUCKET_NAME
    s3 = get_s3_client()

    # Verificar que el bucket exista
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    if bucket_name not in buckets:
        raise RuntimeError(f"El bucket '{bucket_name}' no existe o no es accesible")

    try:
        resp = s3.get_object(Bucket=bucket_name, Key=s3_key)
        return resp["Body"].read()
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        # Ajuste: usar el mismo mensaje que el test espera
        raise RuntimeError(f"No se pudo descargar el objeto '{s3_key}' del bucket '{bucket_name}': {error_code}")
