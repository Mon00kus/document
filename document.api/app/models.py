"""
Modelos de base de datos usando SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    USER = "user"
    ANONYMOUS = "anonymous"


class User(Base):
    """Modelo de usuario"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole),
                  default=UserRole.ANONYMOUS, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FileUpload(Base):
    """Modelo para registrar las cargas de archivos"""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, nullable=False)  # User ID
    param1 = Column(String(255), nullable=True)
    param2 = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())