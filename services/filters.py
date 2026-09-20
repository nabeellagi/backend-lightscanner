import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from core.config import ConversionMode

def to_normal(image: Image.Image) -> Image.Image:
    """Normalize to RGB"""
    return _flatten_to_rgb(image)

def to_black_and_white(image: Image.Image) -> Image.Image:
    """High-contrast black & white for text documents
    """
    rgb = _flatten_to_rgb(image)
    gray = ImageOps.grayscale(rgb)

    gray_arr = np.asarray(gray, dtype=np.float32)
    
    radius = max(15, min(gray.size) // 20)
    local_background = gray.filter(ImageFilter.GaussianBlur(radius=radius))
    bg_arr = np.asarray(local_background, dtype=np.float32)
    
    difference = gray_arr - bg_arr
    binary_arr = np.where(difference < -12, 0, 255).astype(np.uint8)

    binary_image = Image.fromarray(binary_arr, mode="L")
    return binary_image.convert("RGB")

def to_grayscale(image: Image.Image) -> Image.Image:
    """Full grayscale (256 shades) — keeps photographic detail"""
    rgb = _flatten_to_rgb(image)
    gray = ImageOps.grayscale(rgb)
    return gray.convert("RGB")

def to_enhanced_scan(image: Image.Image) -> Image.Image:
    rgb = _flatten_to_rgb(image)
 
    # Normalize lighting first — this fixes photos taken in uneven light
    step = ImageOps.autocontrast(rgb, cutoff=1)
 
    # Push brightness up so the page background reads as bright white
    step = ImageEnhance.Brightness(step).enhance(1.25)
 
    # Increase contrast so text is crisp and dark against the page
    step = ImageEnhance.Contrast(step).enhance(1.4)
 
    # Desaturate partially — real scans rarely have strong color casts
    step = ImageEnhance.Color(step).enhance(0.6)
 
    # Slight sharpening so it doesn't look like a soft photo
    step = ImageEnhance.Sharpness(step).enhance(1.5)
 
    return step

def to_vivid(image: Image.Image) -> Image.Image:
    """Brightens/sharpens like 'enhance', but KEEPS and boosts color
    """
    rgb = _flatten_to_rgb(image)
 
    # Mild brightness lift
    step = ImageEnhance.Brightness(rgb).enhance(1.08)
 
    # Contrast boost for crispness
    step = ImageEnhance.Contrast(step).enhance(1.15)
 
    # Modest sharpening — kept low to avoid JPEG re-encoding artifacts
    step = ImageEnhance.Sharpness(step).enhance(1.15)
 
    # Saturation boost applied LAST, so it isn't diluted
    step = ImageEnhance.Color(step).enhance(1.5)
 
    return step
 
 
def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    """Flatten any transparency onto a white background and convert to RGB.
    """
    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])  # use alpha as mask
        return background
 
    return image.convert("RGB")


FILTER_DISPATCH = {
    ConversionMode.NORMAL: to_normal,
    ConversionMode.BLACK_AND_WHITE: to_black_and_white,
    ConversionMode.GRAYSCALE: to_grayscale,
    ConversionMode.ENHANCE: to_enhanced_scan,
    ConversionMode.VIVID: to_vivid,
}