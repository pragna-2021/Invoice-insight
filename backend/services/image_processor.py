import cv2
import numpy as np

def preprocess_image(img_bytes: bytes) -> np.ndarray:
    """Apply grayscale, noise removal, and contrast enhancement."""
    # Convert bytes to numpy array
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Noise removal (blur)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    
    # Contrast enhancement (thresholding)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh
