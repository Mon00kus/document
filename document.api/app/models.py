"""
Modelos de base de datos usando SQLAlchemy
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, JSON
from sqlalchemy import Index
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """Roles de usuario"""

    ADMIN = "admin"
    USER = "user"
    ANONYMOUS = "anonymous"


class DocumentClassification(str, enum.Enum):
    """Clasificación de documentos"""

    FACTURA = "FACTURA"
    INFORMACION = "INFORMACION"


class User(Base):
    """Modelo de usuario"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ANONYMOUS, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (
        # índice único filtrado: solo aplica si email no es NULL
        Index(
            "ix_users_email_notnull",
            "email",
            unique=True,
            mssql_where="email IS NOT NULL",
        ),
    )


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


class DocumentAnalysis(Base):
    """Modelo para almacenar análisis de documentos con IA"""

    __tablename__ = "document_analysis"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, nullable=False)  # User ID

    # Clasificación del documento
    classification = Column(SQLEnum(DocumentClassification), nullable=False)

    # Datos extraídos (JSON flexible para diferentes tipos de documentos)
    extracted_data = Column(JSON, nullable=True)

    # Campos específicos para facturas
    vendor_name = Column(String(255), nullable=True)
    vendor_address = Column(Text, nullable=True)
    client_name = Column(String(255), nullable=True)
    client_address = Column(Text, nullable=True)
    invoice_number = Column(String(100), nullable=True)
    invoice_date = Column(String(50), nullable=True)
    invoice_total = Column(String(50), nullable=True)

    # Campos específicos para información general
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String(50), nullable=True)  # POSITIVO, NEGATIVO, NEUTRAL

    # Texto completo extraído
    full_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)   # "UPLOAD", "ANALYSIS", "USER_ACTION"
    description = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())