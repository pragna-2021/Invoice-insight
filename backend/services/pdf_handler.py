import fitz  # PyMuPDF

def pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
    """Convert a PDF byte array into a list of image byte arrays."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Increase resolution (default is 72 dpi, 300 dpi is better for OCR)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_bytes = pix.tobytes("png")
        images.append(img_bytes)
        
    return images
