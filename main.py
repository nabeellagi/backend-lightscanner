from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_BATCH,
)
from routers import convert, modes

app = FastAPI(
    title="Image to PDF API",
    description=(
        "Convert batches of JPG/JPEG/PNG images into a single PDF, with "
        "optional filters (black & white, grayscale, or a 'scanned "
        "document' enhance mode).\n\n"
        f"- Max **{MAX_FILES_PER_BATCH} images** per batch\n"
        f"- Max **{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB** per image\n"
        "- Supported formats: JPG, JPEG, PNG"
    ),
    version="1.0.0",
)

app.include_router(modes.router)
app.include_router(convert.router)

app.mount("/test", StaticFiles(directory="static", html=True), name="static")

@app.get("/health", tags=["Health"], summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}