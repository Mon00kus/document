# Document API

API desarrollada con FastAPI para gestión de documentos con autenticación JWT y almacenamiento en S3 (MinIO).

## Características

- **Autenticación JWT**: Sistema de autenticación con tokens JWT (15 minutos de expiración)
- **Carga de archivos CSV**: Endpoint para subir archivos CSV a S3/MinIO
- **Renovación de tokens**: Endpoint para renovar tokens JWT antes de que expiren
- **Base de datos PostgreSQL**: Almacenamiento de usuarios y registros de archivos
- **MinIO**: Simulación de AWS S3 para desarrollo local

## Requisitos

- Docker y Docker Compose
- Python 3.11+ (si se ejecuta localmente)

## Instalación y Ejecución

### Usando Docker Compose (Recomendado)

1. Clonar o navegar al directorio del proyecto:
```bash
cd document.api
```

2. Ejecutar con Docker Compose:
```bash
docker-compose up --build
```

Esto iniciará:
- PostgreSQL en el puerto 5432
- MinIO en los puertos 9000 (API) y 9001 (Consola)
- La API FastAPI en el puerto 8000

3. Acceder a:
- API: http://localhost:8000
- Documentación Swagger: http://localhost:8000/docs
- MinIO Console: http://localhost:9001 (usuario: minioadmin, contraseña: minioadmin)

### Ejecución Local (sin Docker)

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno (copiar `.env.example` a `.env` y ajustar)

3. Asegurarse de que PostgreSQL y MinIO estén corriendo

4. Ejecutar la aplicación:
```bash
uvicorn app.main:app --reload
```

## Endpoints de la API

### 1. Login (`POST /api/v1/login`)
Inicio de sesión para usuarios anónimos. Si el usuario no existe, se crea automáticamente.

**Body (form-data):**
- `username`: Nombre de usuario
- `password`: Contraseña

**Respuesta:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2. Subir CSV (`POST /api/v1/upload-csv`)
Sube un archivo CSV a S3 junto con dos parámetros adicionales.

**Headers:**
- `Authorization: Bearer <token>`

**Body (form-data):**
- `file`: Archivo CSV
- `param1`: Parámetro adicional 1
- `param2`: Parámetro adicional 2

**Respuesta:**
```json
{
  "message": "Archivo subido correctamente",
  "file_id": 1,
  "filename": "archivo.csv",
  "s3_key": "uploads/archivo.csv",
  "param1": "valor1",
  "param2": "valor2"
}
```

### 3. Renovar Token (`POST /api/v1/refresh-token`)
Renueva el token JWT usando el refresh token.

**Body (form-data):**
- `refresh_token`: Token de refresco

**Respuesta:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 4. Información del Usuario (`GET /api/v1/me`)
Obtiene información del usuario autenticado.

**Headers:**
- `Authorization: Bearer <token>`

## Estructura del Proyecto

```
document.api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación principal FastAPI
│   ├── config.py            # Configuración y variables de entorno
│   ├── database.py          # Configuración de SQLAlchemy
│   ├── models.py            # Modelos de base de datos
│   ├── auth_utils.py        # Utilidades de autenticación JWT
│   ├── functions.py         # Funciones auxiliares (S3, validaciones)
│   └── routes.py            # Rutas de la API
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Variables de Entorno

Las variables de entorno se pueden configurar en el archivo `.env` o en `docker-compose.yml`:

- `DATABASE_URL`: URL de conexión a PostgreSQL
- `SECRET_KEY`: Clave secreta para firmar JWT (¡cambiar en producción!)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración del token (default: 15)
- `S3_ENDPOINT_URL`: URL del endpoint S3/MinIO
- `S3_ACCESS_KEY_ID`: Clave de acceso S3
- `S3_SECRET_ACCESS_KEY`: Clave secreta S3
- `S3_BUCKET_NAME`: Nombre del bucket S3

## Desarrollo

Para desarrollo con recarga automática, usar:
```bash
docker-compose up
```

La API se recargará automáticamente cuando se modifiquen los archivos.

## Notas

- Los usuarios anónimos se crean automáticamente al hacer login si no existen
- Los tokens JWT incluyen: ID de usuario, rol y tiempo de expiración
- Los archivos CSV se validan antes de subirse a S3
- MinIO simula AWS S3 para desarrollo local


