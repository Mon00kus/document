"""
Funciones auxiliares para la aplicación
"""
import boto3
from botocore.exceptions import ClientError
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Crea y retorna un cliente de S3 (compatible con MinIO)
    """
    return boto3.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        use_ssl=settings.s3_use_ssl_bool
    )


async def upload_file_to_s3(file_content: bytes, filename: str, bucket: str = None) -> str:
    """
    Sube un archivo a S3/MinIO
    
    Args:
        file_content: Contenido del archivo en bytes
        filename: Nombre del archivo
        bucket: Nombre del bucket (usa el default si es None)
    
    Returns:
        Clave S3 del archivo subido
    
    Raises:
        Exception: Si hay un error al subir el archivo
    """
    if bucket is None:
        bucket = settings.S3_BUCKET_NAME
    
    s3_client = get_s3_client()
    
    try:
        # Asegurar que el bucket existe
        try:
            s3_client.head_bucket(Bucket=bucket)
        except ClientError:
            # El bucket no existe, intentar crearlo
            s3_client.create_bucket(Bucket=bucket)
            logger.info(f"Bucket {bucket} creado")
        
        # Subir el archivo
        s3_key = f"uploads/{filename}"
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_content
        )
        
        logger.info(f"Archivo {filename} subido a S3 con clave {s3_key}")
        return s3_key
        
    except ClientError as e:
        logger.error(f"Error al subir archivo a S3: {e}")
        raise Exception(f"Error al subir archivo a S3: {str(e)}")


def validate_csv_file(file_content: bytes, filename: str) -> bool:
    """
    Valida que el archivo sea un CSV válido
    
    Args:
        file_content: Contenido del archivo
        filename: Nombre del archivo
    
    Returns:
        True si es válido, False en caso contrario
    """
    # Validar extensión
    if not filename.lower().endswith('.csv'):
        return False
    
    # Validar que tenga contenido
    if len(file_content) == 0:
        return False
    
    # Validar que tenga al menos una línea con contenido CSV básico
    try:
        content_str = file_content.decode('utf-8')
        lines = content_str.strip().split('\n')
        if len(lines) == 0:
            return False
        # Verificar que tenga comas o punto y coma (características de CSV)
        if ',' not in lines[0] and ';' not in lines[0]:
            return False
    except UnicodeDecodeError:
        return False
    
    return True

