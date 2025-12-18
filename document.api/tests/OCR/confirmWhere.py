from PIL import Image
import pytesseract

image = Image.open("factura1.png")
text = pytesseract.image_to_string(image, lang="spa+eng")

print(text)