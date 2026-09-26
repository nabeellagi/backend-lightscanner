import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.security import verify_api_key

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

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

if ENVIRONMENT == "production":
    default_origins = "https://lightscanner.vercel.app"
else:
    default_origins = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CLIENT_ORIGINS", default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(modes.router, dependencies=[Depends(verify_api_key)])
app.include_router(convert.router, dependencies=[Depends(verify_api_key)])

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