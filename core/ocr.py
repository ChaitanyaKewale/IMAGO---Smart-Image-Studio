import logging
import pytesseract
from PIL import Image
import platform

logger = logging.getLogger(__name__)

# Windows path hint — adjust if tesseract is elsewhere
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRModule:
    def extract_text(self, image: Image.Image) -> str:
        try:
            rgb = image.convert("RGB")
            text = pytesseract.image_to_string(rgb)
            return text.strip() if text.strip() else "(No text detected)"
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return f"OCR Error: {e}\n\nMake sure Tesseract is installed:\n  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n  Linux: sudo apt install tesseract-ocr\n  Mac: brew install tesseract"

    def save_text(self, text, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        except Exception as e:
            logger.error(f"OCR save error: {e}")
            return False
