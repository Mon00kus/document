import pytest
from moto import mock_aws
from app.services.s3_utils import download_file_from_s3, get_s3_client
from app.config import settings


@mock_aws
def test_download_file_from_s3():
    # Arrange: crear bucket y subir archivo simulado
    s3 = get_s3_client()
    s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
    test_key = "uploads/test.txt"
    test_content = b"Hola Raul, este es un test"
    s3.put_object(Bucket=settings.S3_BUCKET_NAME, Key=test_key, Body=test_content)

    # Act: descargar archivo con nuestra función
    result = download_file_from_s3(test_key)

    # Assert: validar contenido
    assert result == test_content
    assert isinstance(result, bytes)


@mock_aws
def test_download_file_from_s3_with_custom_bucket():
    # Arrange
    custom_bucket = "custom-bucket"
    s3 = get_s3_client()
    s3.create_bucket(Bucket=custom_bucket)
    test_key = "uploads/custom.txt"
    test_content = b"Contenido en bucket custom"
    s3.put_object(Bucket=custom_bucket, Key=test_key, Body=test_content)

    # Act
    result = download_file_from_s3(test_key, bucket=custom_bucket)

    # Assert
    assert result == test_content


@mock_aws
def test_download_file_from_s3_bucket_not_exist():
    # Arrange: no crear el bucket
    test_key = "upload/missing.txt"

    # Act and Assert: debe lanzar RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        download_file_from_s3(test_key, bucket="bucket-inexistente")

    assert "no existe" in str(excinfo.value).lower()


@mock_aws
def test_download_file_from_s3_object_not_exists():
    # Arrange: crear bucket válido pero sin subir el objeto
    s3 = get_s3_client()
    s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
    test_key = "uploads/inexistente.txt"

    # Act & Assert: debe lanzar RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        download_file_from_s3(test_key)

    assert "no se pudo descargar" in str(excinfo.value).lower()
    
from app.services.s3_utils import get_s3_client


def test_get_s3_client_default(monkeypatch):
    monkeypatch.setattr("app.config.settings.AWS_REGION", "us-east-1")
    client = get_s3_client()
    assert client.meta.region_name == "us-east-1"

def test_get_s3_client_with_endpoint(monkeypatch):
    monkeypatch.setattr("app.config.settings.AWS_ENDPOINT_URL", "http://localhost:4566")
    client = get_s3_client()
    assert client.meta.endpoint_url.startswith("http://localhost:4566")
