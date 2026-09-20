"""
Router: POST /mode/{mode}

Handles the actual image-upload -> filter -> PDF conversion for all four modes."""

import io

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, UnidentifiedImageError
from starlette import status
from fastapi import HTTPException

from core.config import ConversionMode
from core.validation import (
    validate_batch_size,
    validate_file_size,
    validate_file_type,
)
from services.filters import FILTER_DISPATCH
from services.pdf_builder import build_pdf_from_images

router = APIRouter(prefix="/mode", tags=["Convert"])


@router.post(
    "/{mode}",
    summary="Convert uploaded images to a PDF using the given mode",
    description=(
        "Upload 1-25 JPG/JPEG/PNG images (max 10 MB each). The images are "
        "processed in the given mode and combined into a single multi-page "
        "PDF, returned directly as a file download. Page order matches "
        "upload order."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "The generated PDF file.",
        },
        400: {"description": "No files uploaded, or too many files."},
        404: {"description": "Unknown conversion mode."},
        413: {"description": "A file exceeded the 10 MB size limit."},
        415: {"description": "A file was not a JPG/JPEG/PNG image."},
        422: {"description": "A file could not be read/decoded as an image."},
    },
)
async def convert_images(
    mode: ConversionMode,
    files: list[UploadFile] = File(
        ...,
        description="1-25 image files (JPG/JPEG/PNG), 10 MB max each.",
    ),
) -> StreamingResponse:
    # Validate the batch as a whole
    validate_batch_size(files)

    filter_fn = FILTER_DISPATCH[mode]

    processed_images: list[Image.Image] = []

    for upload in files:
        validate_file_type(upload)

        raw_bytes = await upload.read()
        validate_file_size(raw_bytes, upload.filename or "unknown")

        try:
            image = Image.open(io.BytesIO(raw_bytes))
            image.load()  # force decode now, so corrupt files fail here,
            # not later during PDF assembly
        except UnidentifiedImageError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not decode '{upload.filename}' as an image.",
            )

        processed = filter_fn(image)
        processed_images.append(processed)

    pdf_bytes = build_pdf_from_images(processed_images)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{mode.value}.pdf"'
        },
    )