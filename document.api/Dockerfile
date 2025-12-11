FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
# Instalar dependencias del sistema y drivers ODBC para SQL Server
# Instalar dependencias del sistema y drivers ODBC para SQL Server
# Debian 12 (Bookworm) is the base for python:3.11-slim
RUN apt-get update && apt-get install -y \
  curl \
  gnupg2 \
  gcc \
  g++ \
  unixodbc-dev \
  && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
  && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
  && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt.dev .
RUN pip install --no-cache-dir -r requirements.txt.dev

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


