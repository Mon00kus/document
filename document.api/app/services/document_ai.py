"""
Servicio de análisis de documentos con IA usando AWS Textract
"""

import boto3
import logging
import re
from typing import Dict, Any, Tuple
from app.config import settings
from app.models import DocumentClassification

logger = logging.getLogger(__name__)


def get_textract_client():
    """
    Crea y retorna un cliente de AWS Textract (compatible con LocalStack)
    """
    return boto3.client(
        "textract",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        use_ssl=settings.s3_use_ssl_bool,
    )


def extract_text_from_document(file_bytes: bytes) -> str:
    """
    Extrae texto de un documento usando AWS Textract

    Args:
        file_bytes: Contenido del archivo en bytes

    Returns:
        Texto extraído del documento
    """
    try:
        textract_client = get_textract_client()

        response = textract_client.detect_document_text(Document={"Bytes": file_bytes})

        # Extraer todo el texto de los bloques
        text_lines = []
        for block in response.get("Blocks", []):
            if block["BlockType"] == "LINE":
                text_lines.append(block["Text"])

        full_text = "\n".join(text_lines)
        logger.info(f"Texto extraído: {len(full_text)} caracteres")

        return full_text

    except Exception as e:
        logger.error(f"Error al extraer texto con Textract: {e}")
        # Fallback: retornar texto vacío si Textract falla
        return ""


def classify_document(text: str) -> DocumentClassification:
    """
    Clasifica el documento como FACTURA o INFORMACION basándose en el contenido

    Args:
        text: Texto del documento

    Returns:
        Clasificación del documento
    """
    text_lower = text.lower()

    # Palabras clave que indican una factura
    invoice_keywords = [
        "factura",
        "invoice",
        "total",
        "subtotal",
        "iva",
        "tax",
        "precio",
        "price",
        "cantidad",
        "quantity",
        "proveedor",
        "vendor",
        "cliente",
        "customer",
        "payment",
        "pago",
        "bill",
        "receipt",
        "recibo",
        "importe",
        "amount",
    ]

    # Contar cuántas palabras clave de factura aparecen
    invoice_score = sum(1 for keyword in invoice_keywords if keyword in text_lower)

    # Si tiene 3 o más palabras clave de factura, clasificar como FACTURA
    if invoice_score >= 3:
        return DocumentClassification.FACTURA

    # Buscar patrones numéricos típicos de facturas (montos, fechas)
    has_currency = bool(re.search(r"[\$€£]\s*\d+", text))
    has_date = bool(re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text))
    has_numbers = bool(re.search(r"\d+[.,]\d{2}", text))

    if (has_currency or has_numbers) and has_date:
        return DocumentClassification.FACTURA

    return DocumentClassification.INFORMACION


def extract_invoice_data(text: str) -> Dict[str, Any]:
    """
    Extrae datos específicos de una factura

    Args:
        text: Texto de la factura

    Returns:
        Diccionario con datos extraídos
    """
    data = {}

    # Extraer número de factura
    invoice_patterns = [
        r"(?:factura|invoice)\s*(?:n[oº°]?|#|num)?:?\s*([A-Z0-9-]+)",
        r"(?:n[oº°]|#)\s*factura:?\s*([A-Z0-9-]+)",
    ]
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(1).strip()
            break

    # Extraer fecha
    date_patterns = [
        r"(?:fecha|date):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_date"] = match.group(1).strip()
            break

    # Extraer total
    total_patterns = [
        r"(?:total|amount):?\s*[\$€£]?\s*([\d,]+\.?\d{0,2})",
        r"(?:total|importe)\s*(?:a\s*pagar)?:?\s*[\$€£]?\s*([\d,]+\.?\d{0,2})",
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data["invoice_total"] = match.group(1).strip()
            break

    # Extraer nombres (proveedor/cliente) - buscar líneas con "nombre" o después de "proveedor"/"cliente"
    vendor_patterns = [
        r"(?:proveedor|vendor|from):?\s*([A-Za-z\s&.,]+?)(?:\n|$)",
        r"(?:empresa|company):?\s*([A-Za-z\s&.,]+?)(?:\n|$)",
    ]
    for pattern in vendor_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            vendor = match.group(1).strip()
            if len(vendor) > 3:  # Evitar matches muy cortos
                data["vendor_name"] = vendor[:100]
                break

    client_patterns = [
        r"(?:cliente|customer|to|bill\s*to):?\s*([A-Za-z\s&.,]+?)(?:\n|$)",
    ]
    for pattern in client_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            client = match.group(1).strip()
            if len(client) > 3:
                data["client_name"] = client[:100]
                break

    return data


def analyze_sentiment(text: str) -> str:
    """
    Analiza el sentimiento del texto (simplificado)

    Args:
        text: Texto a analizar

    Returns:
        Sentimiento: POSITIVO, NEGATIVO, o NEUTRAL
    """
    text_lower = text.lower()

    # Palabras positivas
    positive_words = [
        "excelente",
        "bueno",
        "genial",
        "fantástico",
        "maravilloso",
        "excellent",
        "good",
        "great",
        "fantastic",
        "wonderful",
        "feliz",
        "happy",
        "satisfecho",
        "satisfied",
        "éxito",
        "success",
    ]

    # Palabras negativas
    negative_words = [
        "malo",
        "terrible",
        "horrible",
        "pésimo",
        "deficiente",
        "bad",
        "terrible",
        "horrible",
        "poor",
        "awful",
        "problema",
        "problem",
        "error",
        "fallo",
        "failure",
        "triste",
        "sad",
    ]

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    if positive_count > negative_count and positive_count > 0:
        return "POSITIVO"
    elif negative_count > positive_count and negative_count > 0:
        return "NEGATIVO"
    else:
        return "NEUTRAL"


def generate_summary(text: str, max_length: int = 200) -> str:
    """
    Genera un resumen simple del texto

    Args:
        text: Texto completo
        max_length: Longitud máxima del resumen

    Returns:
        Resumen del texto
    """
    # Tomar las primeras líneas significativas
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Filtrar líneas muy cortas (probablemente no son contenido principal)
    meaningful_lines = [line for line in lines if len(line) > 20]

    if not meaningful_lines:
        meaningful_lines = lines

    # Tomar las primeras líneas hasta alcanzar max_length
    summary = ""
    for line in meaningful_lines[:5]:  # Máximo 5 líneas
        if len(summary) + len(line) > max_length:
            break
        summary += line + " "

    summary = summary.strip()

    if len(summary) > max_length:
        summary = summary[: max_length - 3] + "..."

    return summary or "Sin contenido suficiente para generar resumen."


async def analyze_document(
    file_bytes: bytes, filename: str
) -> Tuple[DocumentClassification, Dict[str, Any]]:
    """
    Analiza un documento completo: extrae texto, clasifica y extrae datos

    Args:
        file_bytes: Contenido del archivo
        filename: Nombre del archivo

    Returns:
        Tupla con (clasificación, datos_extraídos)
    """
    logger.info(f"Iniciando análisis de documento: {filename}")

    # 1. Extraer texto
    full_text = extract_text_from_document(file_bytes)

    if not full_text:
        logger.warning("No se pudo extraer texto del documento")
        # Retornar clasificación por defecto
        return DocumentClassification.INFORMACION, {
            "full_text": "",
            "description": "No se pudo extraer texto del documento",
            "summary": "Documento sin contenido de texto extraíble",
            "sentiment": "NEUTRAL",
        }

    # 2. Clasificar documento
    classification = classify_document(full_text)
    logger.info(f"Documento clasificado como: {classification.value}")

    # 3. Extraer datos según clasificación
    extracted_data = {"full_text": full_text}

    if classification == DocumentClassification.FACTURA:
        # Extraer datos de factura
        invoice_data = extract_invoice_data(full_text)
        extracted_data.update(invoice_data)

    else:  # INFORMACION
        # Generar resumen y análisis de sentimiento
        extracted_data["description"] = full_text[:500]  # Primeros 500 caracteres
        extracted_data["summary"] = generate_summary(full_text)
        extracted_data["sentiment"] = analyze_sentiment(full_text)

    logger.info(f"Análisis completado. Datos extraídos: {list(extracted_data.keys())}")

    return classification, extracted_data
