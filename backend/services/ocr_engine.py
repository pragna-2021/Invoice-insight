import os
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
from . import image_processor

# Configure Tesseract path
TESSERACT_EXE_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESSERACT_EXE_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE_PATH

# Determine local tessdata path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# tessdata is under backend/tessdata
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
TESSDATA_DIR = os.path.join(BACKEND_DIR, "tessdata")

# Set the TESSDATA_PREFIX environment variable so Tesseract finds our custom tessdata path automatically
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

# Fallback translator
translator = GoogleTranslator(source='auto', target='en')

def extract_and_translate(img_bytes: bytes) -> tuple[str, str, float, str, float]:
    """
    Extracts text using pytesseract, computes OCR confidence, detects language,
    and translates if necessary.
    
    Returns (raw_text, translated_text, ocr_accuracy, language, translation_accuracy).
    """
    # 1. Preprocess
    processed_img = image_processor.preprocess_image(img_bytes)
    
    # 2. Extract text (relies on TESSDATA_PREFIX environment variable)
    try:
        raw_text = pytesseract.image_to_string(processed_img, lang="eng+rus")
    except Exception as e:
        print(f"OCR Error with eng+rus: {e}. Trying default english.")
        try:
            raw_text = pytesseract.image_to_string(processed_img, lang="eng")
        except Exception as e2:
            print(f"OCR Error with eng: {e2}")
            raw_text = ""

    if not raw_text.strip():
        return ("", "", 0.0, "en", 100.0)

    # 3. Calculate OCR Confidence (ocr_accuracy)
    ocr_accuracy = 0.0
    try:
        data = pytesseract.image_to_data(processed_img, lang="eng+rus", output_type=pytesseract.Output.DICT)
        confidences = [float(c) for c in data['conf'] if c is not None and int(c) != -1]
        if confidences:
            ocr_accuracy = sum(confidences) / len(confidences)
        else:
            ocr_accuracy = 70.0  # default fallback if no words with confidence
    except Exception as e:
        print(f"Confidence calculation error: {e}")
        ocr_accuracy = 75.0

    # 4. Language Detection & Translation
    # Check if the extracted text contains Cyrillic characters (Russian)
    is_russian = bool(re.search('[а-яА-ЯёЁ]', raw_text))
    
    language = "ru" if is_russian else "en"
    translated_text = raw_text
    translation_accuracy = 100.0
    
    if is_russian:
        try:
            # Split lines to keep structure while translating
            lines = raw_text.split('\n')
            translated_lines = []
            for line in lines:
                if line.strip():
                    # Translate non-empty lines
                    translated_line = translator.translate(line)
                    translated_lines.append(translated_line)
                else:
                    translated_lines.append("")
            translated_text = "\n".join(translated_lines)
            validation_accuracy = 95.0  # default translation accuracy
        except Exception as e:
            print(f"Translation error: {e}")
            translated_text = raw_text
            translation_accuracy = 50.0  # translation failed fallback
            
    return raw_text, translated_text, ocr_accuracy, language, translation_accuracy
