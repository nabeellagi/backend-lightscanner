import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        "- Supported formats: JPG, JPEG, PNG, WEBP"
    ),
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CLIENT_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(modes.router)
app.include_router(convert.router)

app.mount(
    "/test",
    StaticFiles(directory="static", html=True),
    name="static",
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
def health() -> dict[str, str]:
    return {"status": "ok"}