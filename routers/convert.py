"""
Router: POST /mode/{mode}

Handles image upload -> filter -> PDF conversion for all supported modes.
The frontend may also send page/layout settings as a JSON multipart field.
"""

import io
import json

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from PIL import Image, UnidentifiedImageError
from starlette import status
from core.config import (
    CM_PER_INCH,
    CUSTOM_PAGE_MAX_CM,
    CUSTOM_PAGE_MIN_CM,
    FIT_PAGE_MAX_LONG_SIDE_IN,
    PAGE_SIZE_CUSTOM,
    PAGE_SIZE_FIT,
    PAGE_SIZE_TOLERANCE_IN,
    ConversionMode,
)
from core.validation import (
    validate_batch_size,
    validate_file_size,
    validate_file_type,
)
from services.filters import FILTER_DISPATCH
from services.pdf_builder import build_pdf_from_images

router = APIRouter(
    prefix="/mode",
    tags=["Convert"],
)


class ImageLayout(BaseModel):
    """Client-calculated layout for one image."""

    index: int = Field(ge=0)

    filename: str

    widthPx: int = Field(gt=0)
    heightPx: int = Field(gt=0)

    renderedWidthIn: float = Field(gt=0)
    renderedHeightIn: float = Field(gt=0)

    marginXIn: float = Field(ge=0)
    marginYIn: float = Field(ge=0)

    pageWidthIn: float | None = Field(default=None, gt=0, le=100)
    pageHeightIn: float | None = Field(default=None, gt=0, le=100)


class ConversionSettings(BaseModel):
    """Page and per-image layout settings."""

    pageSizeId: str
    orientation: str

    pageWidthIn: float = Field(
        gt=0,
        le=100,
    )

    pageHeightIn: float = Field(
        gt=0,
        le=100,
    )

    images: list[ImageLayout]


def _validate_custom_page(settings: "ConversionSettings") -> None:
    """Custom page sizes must stay between 10 cm and 60 cm per side."""
    min_in = CUSTOM_PAGE_MIN_CM / CM_PER_INCH
    max_in = CUSTOM_PAGE_MAX_CM / CM_PER_INCH

    for label, value in (
        ("width", settings.pageWidthIn),
        ("height", settings.pageHeightIn),
    ):
        if (
            value < min_in - PAGE_SIZE_TOLERANCE_IN
            or value > max_in + PAGE_SIZE_TOLERANCE_IN
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Custom page {label} must be between "
                    f"{CUSTOM_PAGE_MIN_CM:g} and "
                    f"{CUSTOM_PAGE_MAX_CM:g} cm."
                ),
            )


def _validate_fit_page(settings: "ConversionSettings") -> None:
    """Fit-to-page"""
    for item in settings.images:
        if item.pageWidthIn is None or item.pageHeightIn is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Image {item.index + 1} is missing its "
                    "fit-to-page size."
                ),
            )

        longest = max(item.pageWidthIn, item.pageHeightIn)

        if longest > FIT_PAGE_MAX_LONG_SIDE_IN + PAGE_SIZE_TOLERANCE_IN:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Fit-to-page size for image {item.index + 1} "
                    "is too large."
                ),
            )


def parse_settings(
    raw_settings: str | None,
    image_count: int,
) -> ConversionSettings | None:
    """
    Parse optional JSON metadata.

    It remains optional so your existing test upload endpoint
    continues to work.
    """

    if raw_settings is None:
        return None

    try:
        settings = (
            ConversionSettings.model_validate_json(
                raw_settings
            )
        )

    except (
        ValidationError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid conversion settings: {exc}",
        ) from exc

    if len(settings.images) != image_count:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Settings describe "
                f"{len(settings.images)} images, "
                f"but {image_count} files were uploaded."
            ),
        )

    expected_indexes = list(
        range(image_count)
    )

    actual_indexes = [
        item.index
        for item in settings.images
    ]

    if actual_indexes != expected_indexes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Image layout indexes must match "
                "upload order."
            ),
        )

    if settings.orientation not in {
        "portrait",
        "landscape",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Orientation must be "
                "'portrait' or 'landscape'."
            ),
        )

    if settings.pageSizeId == PAGE_SIZE_CUSTOM:
        _validate_custom_page(settings)

    if settings.pageSizeId == PAGE_SIZE_FIT:
        _validate_fit_page(settings)

    elif any(
        item.pageWidthIn is not None
        or item.pageHeightIn is not None
        for item in settings.images
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Per-image page sizes are only allowed "
                "with the 'fit' page size."
            ),
        )

    for item in settings.images:
        # Fit-to-page images carry their own page size.
        page_width_in = (
            item.pageWidthIn
            if item.pageWidthIn is not None
            else settings.pageWidthIn
        )

        page_height_in = (
            item.pageHeightIn
            if item.pageHeightIn is not None
            else settings.pageHeightIn
        )

        expected_margin_x = (
            page_width_in
            - item.renderedWidthIn
        ) / 2

        expected_margin_y = (
            page_height_in
            - item.renderedHeightIn
        ) / 2

        if (
            expected_margin_x < -0.01
            or expected_margin_y < -0.01
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Image {item.index + 1} "
                    "is larger than the requested page."
                ),
            )

        if abs(
            expected_margin_x
            - item.marginXIn
        ) > 0.05:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Horizontal margin for image "
                    f"{item.index + 1} is inconsistent."
                ),
            )

        if abs(
            expected_margin_y
            - item.marginYIn
        ) > 0.05:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Vertical margin for image "
                    f"{item.index + 1} is inconsistent."
                ),
            )

    return settings


@router.post(
    "/{mode}",
    summary="Convert uploaded images to a PDF using the given mode",
    description=(
        "Upload 1-25 JPG/JPEG/PNG/WEBP images "
        "(max 10 MB each). The images are processed "
        "in the given mode and combined into a single "
        "multi-page PDF."
    ),
    responses={
        200: {
            "content": {
                "application/pdf": {}
            },
            "description": "The generated PDF file.",
        },
        400: {
            "description":
                "No files uploaded, or too many files."
        },
        404: {
            "description":
                "Unknown conversion mode."
        },
        413: {
            "description":
                "A file exceeded the 10 MB size limit."
        },
        415: {
            "description":
                "Unsupported image type."
        },
        422: {
            "description":
                "A file or conversion settings "
                "could not be decoded."
        },
    },
)
async def convert_images(
    mode: ConversionMode,

    files: list[UploadFile] = File(
        ...,
        description=(
            "1-25 image files "
            "(JPG/JPEG/PNG/WEBP), "
            "10 MB max each."
        ),
    ),

    settings: str | None = Form(
        default=None,
        description=(
            "Optional JSON containing page size, "
            "orientation, and per-image layout."
        ),
    ),
) -> StreamingResponse:

    validate_batch_size(files)

    conversion_settings = parse_settings(
        settings,
        len(files),
    )

    filter_fn = FILTER_DISPATCH[mode]

    processed_images: list[
        Image.Image
    ] = []

    for upload in files:
        validate_file_type(upload)

        raw_bytes = await upload.read()

        validate_file_size(
            raw_bytes,
            upload.filename or "unknown",
        )

        try:
            image = Image.open(
                io.BytesIO(raw_bytes)
            )

            image.load()

        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    f"Could not decode "
                    f"'{upload.filename}' "
                    "as an image."
                ),
            ) from exc

        processed = filter_fn(image)

        processed_images.append(
            processed
        )

    pdf_bytes = build_pdf_from_images(
        processed_images,
        settings=(
            conversion_settings.model_dump()
            if conversion_settings
            else None
        ),
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="lightscanner-{mode.value}.pdf"'
            )
        },
    )