import os
import sys
from pdf2image import convert_from_bytes
import pytesseract
import pdfplumber
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_document(file_path: str) -> str:
    """
    Extrae texto de un archivo local (PDF o imagen) usando librerías locales.
    """
    try:
        if file_path.lower().endswith(".pdf"):
          
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        
                if text.strip():
                  return text.strip()
                
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            images = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=r"D:\poppler-25.12.0\Library\bin")
            ocr_text = ""
            for img in images:
                ocr_text += pytesseract.image_to_string(img, lang="spa+eng") + "\n"

            return ocr_text.strip()

        else:  # Imagen (JPG, PNG)
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="spa+eng")
            return text.strip()

    except Exception as e:
        print(f"Error al extraer texto: {e}")
        return ""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_extract_text.py <ruta_al_archivo>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Archivo no encontrado: {file_path}")
        sys.exit(1)

    extracted_text = extract_text_from_document(file_path)

    print("=== TEXTO EXTRAÍDO ===")
    print(extracted_text)
    print("=== FIN DEL TEXTO ===")