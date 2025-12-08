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
    create_refresh_token
)
from app.functions import upload_file_to_s3, validate_csv_file
from app.config import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
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
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/login", summary="Inicio de sesión para usuarios anónimos")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de inicio de sesión que permite a usuarios anónimos iniciar sesión.
    Si el usuario no existe, se crea automáticamente con rol ANONYMOUS.
    
    Devuelve un JWT con:
    - ID del usuario
    - Rol
    - Tiempo de expiración de 15 minutos
    """
    # Buscar usuario por username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # Si el usuario no existe, crear uno nuevo con rol ANONYMOUS
    if user is None:
        user = User(
            username=form_data.username,
            password_hash=get_password_hash(form_data.password),
            role=UserRole.ANONYMOUS
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"Usuario anónimo creado: {user.username}")
    else:
        # Verificar contraseña
        if not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
    
    # Crear token de acceso
    access_token = create_access_token(
        data={
            "sub": user.id,
            "role": user.role.value
        }
    )
    
    # Crear token de refresco
    refresh_token = create_refresh_token(
        data={
            "sub": user.id,
            "role": user.role.value
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/upload-csv", summary="Subir archivo CSV a S3")
async def upload_csv(
    file: UploadFile = File(..., description="Archivo CSV a subir"),
    param1: str = Form(..., description="Parámetro adicional 1"),
    param2: str = Form(..., description="Parámetro adicional 2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
            detail="El archivo debe ser un CSV válido"
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
            param2=param2
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
            "param2": param2
        }
        
    except Exception as e:
        logger.error(f"Error al subir archivo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo: {str(e)}"
        )


@router.post("/refresh-token", summary="Renovar token JWT")
async def refresh_token(
    refresh_token: str = Form(...),
    db: AsyncSession = Depends(get_db)
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
            detail="Token de refresco inválido o expirado"
        )
    
    # Verificar que sea un token de refresco
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no es un token de refresco válido"
        )
    
    # Obtener información del usuario
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if user_id is None or role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido"
        )
    
    # Verificar que el usuario aún existe
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    # Crear nuevo token de acceso
    new_access_token = create_access_token(
        data={
            "sub": user.id,
            "role": user.role.value
        }
    )
    
    # Crear nuevo token de refresco
    new_refresh_token = create_refresh_token(
        data={
            "sub": user.id,
            "role": user.role.value
        }
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", summary="Obtener información del usuario actual")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obtener información del usuario autenticado
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value
    }

