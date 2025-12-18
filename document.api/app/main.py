"""
Aplicación principal FastAPI
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import router
from app.config import settings

# Configurar logging
""" logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__) """

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger()


# Crear instancia de FastAPI
app = FastAPI(
    title="Document API",
    version="1.0.1",
    description="API para gestión de documentos con autenticación JWT y almacenamiento en S3"
)


# Activa Authorized en swagger
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="Document API",
        version="1.0.1",
        description="API para gestión de documentos con autenticación JWT y almacenamiento en S3",
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Aplicar seguridad a todas las rutas excepto login y refresh-token
    for path, methods in openapi_schema["paths"].items():
        if path not in ["/login", "/refresh-token", "/openapi.json", "/docs", "/redoc"]:
            for method in methods.values():
                if isinstance(method, dict):
                    method.setdefault("security", [{"OAuth2PasswordBearer": []}])
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicio para la conexión a la DB
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación...")
    await asyncio.sleep(2)  # Esperar a que la base de datos esté lista
    await init_db()
    logger.info("Aplicación iniciada correctamente")


# Incluir las rutas desde el archivo routes.py
app.include_router(router, prefix="/api/v1", tags=["API"])


@app.get("/", tags=["Health"])
async def root():
    """Endpoint de salud"""
    return {"message": "Document API está funcionando", "version": "1.0.1"}


@app.get("/health", tags=["Health"])
async def health():
    """Endpoint de salud detallado"""
    return {
        "status": "healthy",
        "version": "1.0.1"
    }


