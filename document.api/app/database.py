"""
Configuración de la base de datos usando SQLAlchemy con PostgreSQL
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Base para los modelos
Base = declarative_base()

# Motor de base de datos asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """
    Dependency para obtener una sesión de base de datos
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Inicializa la base de datos creando todas las tablas
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise


