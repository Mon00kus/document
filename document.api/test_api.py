"""
Script de ejemplo para probar la API
Ejecutar después de iniciar los servicios con docker-compose
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_login():
    """Prueba el endpoint de login"""
    print("=== Probando Login ===")
    response = requests.post(
        f"{BASE_URL}/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.status_code == 200 else None


def test_upload_csv(token):
    """Prueba el endpoint de carga de CSV"""
    print("\n=== Probando Upload CSV ===")

    # Crear un archivo CSV de ejemplo
    csv_content = "nombre,edad,ciudad\nJuan,25,Madrid\nMaría,30,Barcelona"

    files = {
        'file': ('test.csv', csv_content, 'text/csv')
    }
    data = {
        'param1': 'valor1',
        'param2': 'valor2'
    }
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.post(
        f"{BASE_URL}/upload-csv",
        files=files,
        data=data,
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_refresh_token(refresh_token):
    """Prueba el endpoint de renovación de token"""
    print("\n=== Probando Refresh Token ===")
    response = requests.post(
        f"{BASE_URL}/refresh-token",
        data={
            "refresh_token": refresh_token
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json() if response.status_code == 200 else None


def test_me(token):
    """Prueba el endpoint de información del usuario"""
    print("\n=== Probando GET /me ===")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(
        f"{BASE_URL}/me",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    print("Iniciando pruebas de la API...")
    print("Asegúrate de que los servicios estén corriendo con: docker-compose up\n")

    # 1. Login
    login_response = test_login()
    if not login_response:
        print("Error en login, abortando pruebas")
        exit(1)

    access_token = login_response["access_token"]
    refresh_token = login_response["refresh_token"]

    # 2. Obtener información del usuario
    test_me(access_token)

    # 3. Subir CSV
    test_upload_csv(access_token)

    # 4. Renovar token
    refresh_response = test_refresh_token(refresh_token)
    if refresh_response:
        new_access_token = refresh_response["access_token"]
        test_me(new_access_token)

    print("\n=== Pruebas completadas ===")
