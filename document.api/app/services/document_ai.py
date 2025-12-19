"""
Servicio de análisis de documentos con IA usando AWS Textract
"""
import boto3
import logging
import re
from PIL import Image, ImageOps, ImageFilter

import io
import pdfplumber

from typing import Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models import DocumentClassification
from app.functions import log_event

from pdf2image import convert_from_bytes
import pytesseract
import numpy as np

import unicodedata


#logger = logging.getLogger(__name__)
logger = logging.getLogger("document_ai")  # o el nombre del módulo


#pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "tesseract"


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


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    # Eliminar canal alpha si existe
    if image.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[-1])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Convertir a escala de grises
    image = image.convert("L")

    # Aumentar resolución (hasta 2x, límite razonable)
    scale = 2
    image = image.resize(
        (image.width * scale, image.height * scale), Image.LANCZOS)

    # Contraste y nitidez
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.UnsharpMask(
        radius=2, percent=150, threshold=3))

    # Binarización por umbral de Otsu (simple aproximación)
    arr = np.array(image)
    thresh = arr.mean()  # aproximación; para Otsu real usar skimage si lo tienes
    binarized = (arr > thresh).astype(np.uint8) * 255
    image = Image.fromarray(binarized, mode="L")

    return image


def extract_text_from_document(file_bytes: bytes, filename: str) -> str:
    """
    Extrae texto de un documento usando librerías locales:
    - PDF → pdfplumber (texto embebido) o OCR con pdf2image
    - Imagen (JPG/PNG) → pytesseract (OCR)
    """
    try:
        if filename.lower().endswith(".pdf"):
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if text.strip():
                return text.strip()

            # Si no hay texto embebido, usar OCR
            images = convert_from_bytes(
                file_bytes, dpi=300, poppler_path=r"D:\poppler-25.12.0\Library\bin")
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(
                    img, lang="spa+eng") + "\n"

            return ocr_text.strip()

        else:  # Imagen (JPG, PNG)

            image = Image.open(io.BytesIO(file_bytes))
            image = preprocess_for_ocr(image)

            # Configurar Tesseract: psm 6 (asume bloque uniforme), OEM 1 (LSTM)
            config = "--psm 6 --oem 1"
            text = pytesseract.image_to_string(
                image, lang="spa+eng", config=config)  # .strip()

            if len(text) < 60:
                alt_config = "--psm 4 --oem 1"
                text = pytesseract.image_to_string(
                    image, lang="spa+eng", config=alt_config)  # .strip()

            return text

    except Exception as e:
        logger.error(f"Error al extraer texto: {e}")
        return ""


def normalize_text(text: str) -> str:
    # Elimina acentos y caracteres especiales
    norm = unicodedata.normalize("NFKD", text)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    # Sustituye símbolos raros por espacios
    norm = re.sub(r"[^a-zA-Z0-9\s.,:/-]", " ", norm)
    # Minúsculas y espacios colapsados
    norm = " ".join(norm.lower().split())
    return norm

    """ norm = unicodedata.normalize("NFKD", text)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = " ".join(norm.lower().split())
    return norm """


def classify_document(text: str) -> DocumentClassification:
    text_lower = normalize_text(text)

    invoice_keywords = [
        "factura", "invoice", "comprobante", "orden de compra", "cotizacion",
        "total", "subtotal", "iva", "tax", "precio", "price", "cantidad", "quantity",
        "proveedor", "vendor", "cliente", "customer", "payment", "pago", "bill",
        "recibo", "importe", "amount", "numero de factura", "fecha de emision",
        "rif", "bs", "bolivares", "transferencia", "forma de pago"
    ]

    invoice_score = sum(
        1 for keyword in invoice_keywords if keyword in text_lower)

    has_currency = bool(
        re.search(r"(bs|bolivares|\$|€|£)\s*\d[\d.,]*", text_lower))
    has_date = bool(
        re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text_lower))
    has_invoice_number = bool(
        re.search(r"(factura|invoice)[^\n]{0,40}\b[a-z0-9-]{3,}\b", text_lower))
    has_amount_grid = len(re.findall(r"\b\d+[.,]\d{2}\b", text_lower)) >= 3

    signals = sum([
        invoice_score >= 3,
        has_currency,
        has_date,
        has_invoice_number,
        has_amount_grid
    ])

    if signals >= 3:
        return DocumentClassification.FACTURA

    if invoice_score >= 3:
        return DocumentClassification.FACTURA

    if (has_currency or has_amount_grid) and has_date:
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
    db: AsyncSession,    
    file_bytes: bytes, 
    file_path: str
) -> Tuple[DocumentClassification, Dict[str, Any]]:
    """
    Analiza un documento completo: extrae texto, clasifica y extrae datos.

    Args:
        file_bytes: Contenido del archivo
        file_path: Nombre del archivo

    Returns:
        Tupla con (clasificación, datos_extraídos)
    """
    logger.info(f"Iniciando análisis de documento: {file_path}")

    # 1. Extraer texto con OCR / pdfplumber
    full_text = extract_text_from_document(file_bytes, file_path)

    if not full_text:
        logger.warning("No se pudo extraer texto del documento")
											 
        return DocumentClassification.INFORMACION, {
            "full_text": "",
            "description": "No se pudo extraer texto del documento",
            "summary": "Documento sin contenido de texto extraíble",
            "sentiment": "NEUTRAL",
        }

    # 2. Clasificar documento
    classification = classify_document(full_text)
    logger.info(f"OCR length: {len(full_text)}")
    logger.info(f"OCR preview:\n{full_text[:500]}")
    logger.info(f"Documento clasificado como: {classification.value}")

    # 3. Extraer datos según clasificación
    extracted_data: Dict[str, Any] = {"full_text": full_text}

    if classification == DocumentClassification.FACTURA:
								  
        invoice_data = extract_invoice_data(full_text)
        extracted_data.update(invoice_data)

    else:  # INFORMACION
													
								 
        extracted_data["description"] = full_text[:500]
        extracted_data["summary"] = generate_summary(full_text)
        extracted_data["sentiment"] = analyze_sentiment(full_text)

				
    logger.info(f"Análisis completado. Datos extraídos: {list(extracted_data.keys())}")
    
    await log_event(
      db,
      event_type="ANALYSIS",
      description=f"Documento {file_path} clasificado como {classification}"
    )


    # ✅ Return corregido: solo dos valores
    return classification, extracted_data
