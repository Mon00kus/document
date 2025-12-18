"""
Rutas de la API
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.database import get_db
from app.models import User, UserRole, FileUpload
from app.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    create_refresh_token,
)
from app.functions import upload_file_to_s3, validate_csv_file
from app.config import settings
from datetime import timedelta
import logging
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


#logger = logging.getLogger(__name__)

logger = logging.getLogger("routes")  # o el nombre del módulo

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency para obtener el usuario actual desde el token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    user_id: int = int(user_id_str)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


@router.post("/login", summary="Inicio de sesión para usuarios anónimos")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Endpoint de inicio de sesión que permite a usuarios anónimos iniciar sesión.
    Si el usuario no existe, se crea automáticamente con rol ANONYMOUS.

    Devuelve un JWT con:
    - ID del usuario
    - Rol
    - Tiempo de expiración de 15 minutos
    """
    # Buscar usuario por username
    result = await db.execute(select(User).where(User.username == login_data.username))
    user = result.scalar_one_or_none()

    # Si el usuario no existe, crear uno nuevo con rol ANONYMOUS
    if user is None:
        user = User(
            username=login_data.username,
            password_hash=get_password_hash(login_data.password),
            role=UserRole.ANONYMOUS,
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        logger.info(f"Usuario anónimo creado: {user.username}")
    else:
        # Verificar contraseña
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos",
            )

    # Crear token de acceso
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    # Crear token de refresco
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/upload-csv", summary="Subir archivo CSV a S3")
async def upload_csv(
    file: UploadFile = File(..., description="Archivo CSV a subir"),
    param1: str = Form(..., description="Parámetro adicional 1"),
    param2: str = Form(..., description="Parámetro adicional 2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint para subir un archivo CSV junto con dos parámetros adicionales.
    El archivo se almacena en AWS S3 (o MinIO).

    Requisitos:
    - El usuario debe estar autenticado
    - El archivo debe ser un CSV válido
    """
    # Leer el contenido del archivo
    file_content = await file.read()

    # Validar que sea un CSV
    if not validate_csv_file(file_content, file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un CSV válido",
        )

    try:
        # Subir a S3
        s3_key = await upload_file_to_s3(file_content, file.filename)

        # Registrar en la base de datos
        file_upload = FileUpload(
            filename=file.filename,
            s3_key=s3_key,
            s3_bucket=settings.S3_BUCKET_NAME,
            file_size=len(file_content),
            uploaded_by=current_user.id,
            param1=param1,
            param2=param2,
        )

        db.add(file_upload)
        await db.commit()
        await db.refresh(file_upload)

        return {
            "message": "Archivo subido correctamente",
            "file_id": file_upload.id,
            "filename": file.filename,
            "s3_key": s3_key,
            "param1": param1,
            "param2": param2,
        }

    except Exception as e:
        logger.error(f"Error al subir archivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}",
        )


@router.post("/refresh-token", summary="Renovar token JWT")
async def refresh_token(
    refresh_token: str = Form(...), db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para renovar el JWT, generando un nuevo token con tiempo de expiración adicional.
    Solo puede ser accedido si el token de refresco aún no ha expirado.
    """
    # Decodificar el token de refresco
    payload = decode_token(refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado",
        )

    # Verificar que sea un token de refresco
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no es un token de refresco válido",
        )

    # Obtener información del usuario
    user_id_str = payload.get("sub")
    role = payload.get("role")

    if user_id_str is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido",
        )

    user_id = int(user_id_str)

    # Verificar que el usuario aún existe
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado"
        )

    # Crear nuevo token de acceso
    new_access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    # Crear nuevo token de refresco
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "role": user.role.value}
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.get("/me", summary="Obtener información del usuario actual")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Endpoint para obtener información del usuario autenticado
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
    }


@router.post("/upload-document", summary="Subir y analizar documento con IA")
async def upload_document(
    file: UploadFile = File(..., description="Documento PDF, JPG o PNG para análisis"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint para subir y analizar documentos con IA.

    Funcionalidades:
    - Clasifica automáticamente como FACTURA o INFORMACION
    - Si es FACTURA: extrae cliente, proveedor, número, fecha, productos, total
    - Si es INFORMACION: extrae descripción, resumen, análisis de sentimiento

    Formatos soportados: PDF, JPG, PNG
    """
    from app.services.document_ai import analyze_document
    from app.models import DocumentAnalysis

    # Validar tipo de archivo
    allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png"]
    file_ext = (
        "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    )

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no soportado. Use: {', '.join(allowed_extensions)}",
        )

    try:
        # Leer el contenido del archivo
        file_content = await file.read()
        
        logger.info("⚡ Upload document iniciado")
        logger.info(f"Tamaño del archivo recibido: {len(file_content)} bytes")

        # Subir a S3
        s3_key = await upload_file_to_s3(file_content, file.filename)
        
        classification, extracted_data = await analyze_document(
            file_content, file.filename
        )
        
        param1 = "FACTURACION" if classification.value == "FACTURA" else "DOCUMENTACION"
        param2 = "PENDIENTE_REVISION"
        
        # Registrar en file_uploads
        file_upload = FileUpload(
            filename=file.filename,
            s3_key=s3_key,
            s3_bucket=settings.S3_BUCKET_NAME,
            file_size=len(file_content),
            uploaded_by=current_user.id,
            param1=param1,
            param2=param2,
        )
        db.add(file_upload)
        await db.flush()  # para obtener file_upload.id sin hacer commit

        # Analizar documento con IA
        classification, extracted_data = await analyze_document(
            file_content, file.filename
        )

        # Crear registro en la base de datos
        document_analysis = DocumentAnalysis(
            filename=file.filename,
            s3_key=s3_key,
            s3_bucket=settings.S3_BUCKET_NAME,
            file_size=len(file_content),
            uploaded_by=current_user.id,
            classification=classification,
            extracted_data=extracted_data,
            full_text=extracted_data.get("full_text", ""),
            # Datos de factura
            vendor_name=extracted_data.get("vendor_name"),
            vendor_address=extracted_data.get("vendor_address"),
            client_name=extracted_data.get("client_name"),
            client_address=extracted_data.get("client_address"),
            invoice_number=extracted_data.get("invoice_number"),
            invoice_date=extracted_data.get("invoice_date"),
            invoice_total=extracted_data.get("invoice_total"),
            # Datos de información
            description=extracted_data.get("description"),
            summary=extracted_data.get("summary"),
            sentiment=extracted_data.get("sentiment"),
        )

        db.add(document_analysis)
        await db.commit()
        await db.refresh(document_analysis)

        # Preparar respuesta según clasificación
        response_data = {
            "message": "Documento analizado correctamente",
            "analysis_id": document_analysis.id,
            "filename": file.filename,
            "s3_key": s3_key,
            "classification": classification.value,
            "data": {},
        }

        if classification.value == "FACTURA":
            response_data["data"] = {
                "vendor_name": document_analysis.vendor_name,
                "vendor_address": document_analysis.vendor_address,
                "client_name": document_analysis.client_name,
                "client_address": document_analysis.client_address,
                "invoice_number": document_analysis.invoice_number,
                "invoice_date": document_analysis.invoice_date,
                "invoice_total": document_analysis.invoice_total,
            }
        else:  # INFORMACION
            response_data["data"] = {
                "description": document_analysis.description,
                "summary": document_analysis.summary,
                "sentiment": document_analysis.sentiment,
            }

        return response_data

    except Exception as e:
        logger.error(f"Error al analizar documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al analizar documento: {str(e)}",
        )
