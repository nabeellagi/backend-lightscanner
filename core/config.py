"""
Central configuration for the Image-to-PDF API.
 
Keeping limits and constants here means routers/services never hardcode magic numbers 
"""
from enum import Enum

class ConversionMode(str, Enum):
    """Available conversion modes. The string value is used in the URL path,
    """
    
    NORMAL = "normal"
    BLACK_AND_WHITE = "black-and-white"
    GRAYSCALE = "grayscale"
    ENHANCE = "enhance"
    VIVID = "vivid"

MODE_DESCRIPTIONS: dict[str, str] = {
    ConversionMode.NORMAL: "Direct image to PDF conversion, no filtering applied.",
    ConversionMode.BLACK_AND_WHITE: (
        "Converts to pure black & white (1-bit, high contrast threshold). "
        "Good for text documents / photocopies."
    ),
    ConversionMode.GRAYSCALE: (
        "Converts to full grayscale (256 shades of gray), preserving tonal detail."
    ),
    ConversionMode.ENHANCE: (
        "Simulates a clean scanned document: brightens the page, boosts "
        "contrast, and desaturates toward white so it looks like a real scan "
        "rather than a photo of paper."
    ),
    ConversionMode.VIVID: (
        "Brightens and sharpens like a real photo enhancement, but keeps "
        "(and boosts) original color saturation — for colorful documents, "
        "photos, or artwork where you want vibrant color, not a gray/white "
        "scanned-paper look."
    ),
}

# Upload Constraint

MAX_FILES_PER_BATCH: int = 25
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024 # 10MB

ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

ALLOWED_EXTENSIONS: set[str] = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}