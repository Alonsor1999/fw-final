from PIL import Image
import pytesseract
import cv2
import numpy as np
import io
import random
from config import TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def preprocess_image(image_bytes):
    """Escala de grises + binarizado + eliminación de ruido"""
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    img_array = np.array(image)

    # 1. Eliminar ruido con desenfoque
    blurred = cv2.GaussianBlur(img_array, (3, 3), 0)

    # 2. Binarización con Otsu (mejor adaptación)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. (opcional) Erosión para reducir grosor de líneas
    kernel = np.ones((2, 2), np.uint8)
    morph = cv2.erode(thresh, kernel, iterations=1)

    return Image.fromarray(morph)


def solve_with_tesseract(image_bytes):
    image = preprocess_image(image_bytes)
    raw_text = pytesseract.image_to_string(image, config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    image.save(f".\debug_captcha_{random.randint(1000,9999)}.png")
    return raw_text.strip()
