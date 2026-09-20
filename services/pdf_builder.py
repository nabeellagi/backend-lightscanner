"""Builds a multi-page PDF from a list of PIL Images, entirely in memory.
"""

import io
import img2pdf
from PIL import Image

def build_pdf_from_images(images: list[Image.Image]) -> bytes:
    """Convert a list of RGB PIL Images into a single multi-page PDF.
    Each image becomes one PDF page, in the order given.
    """
    if not images:
        raise ValueError("build_pdf_from_images requires at least one image.")
 
    # Re-encode each image to JPEG in memory first. JPEG is used
    # rather than PNG to keep output file size reasonable.
    
    encoded_pages: list[bytes] = []
    for image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=92)
        encoded_pages.append(buffer.getvalue())
 
    pdf_bytes = img2pdf.convert(encoded_pages)
    return pdf_bytes