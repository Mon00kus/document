"""
Script de prueba para el endpoint de análisis de documentos con IA
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"


def test_document_analysis():
    """Prueba el endpoint de análisis de documentos"""
    print("=== Probando Análisis de Documentos con IA ===\n")

    # 1. Login para obtener token
    print("1. Iniciando sesión...")
    login_response = requests.post(
        f"{BASE_URL}/login", json={"username": "testuser", "password": "testpass123"}
    )

    if login_response.status_code != 200:
        print(f"Error en login: {login_response.status_code}")
        print(login_response.json())
        return

    access_token = login_response.json()["access_token"]
    print("✓ Login exitoso\n")

    # 2. Crear un documento de prueba (factura simulada)
    print("2. Creando documento de prueba...")
    test_document_content = """
    FACTURA
    
    TechCorp Solutions
    Calle Principal 123
    Madrid, España
    
    Factura N°: INV-2024-001
    Fecha: 12/12/2024
    
    Cliente:
    Juan Pérez
    Avenida Libertad 456
    Barcelona, España
    
    Descripción                 Cantidad    Precio Unit.    Total
    --------------------------------------------------------
    Laptop Dell XPS 15         1           $999.00         $999.00
    Mouse Inalámbrico          2           $25.00          $50.00
    Teclado Mecánico           1           $150.00         $150.00
    
    Subtotal:                                              $1,199.00
    IVA (21%):                                             $251.79
    
    TOTAL:                                                 $1,450.79
    
    Gracias por su compra!
    """.encode(
        "utf-8"
    )

    # 3. Subir y analizar documento
    print("3. Subiendo y analizando documento...\n")

    files = {"file": ("factura_test.txt", test_document_content, "text/plain")}
    headers = {"Authorization": f"Bearer {access_token}"}

    # Nota: Usamos .txt para simular, pero el endpoint real acepta PDF, JPG, PNG
    # Para una prueba real, necesitarías un archivo PDF o imagen real

    response = requests.post(
        f"{BASE_URL}/upload-document", files=files, headers=headers
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\n✓ Documento analizado correctamente!\n")
        print(f"ID de Análisis: {result['analysis_id']}")
        print(f"Clasificación: {result['classification']}")
        print(f"\nDatos extraídos:")
        print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    else:
        print(f"\n✗ Error al analizar documento:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("Iniciando pruebas de análisis de documentos con IA...")
    print("Asegúrate de que los servicios estén corriendo\n")

    test_document_analysis()

    print("\n=== Pruebas completadas ===")
