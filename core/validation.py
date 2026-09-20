import os

from fastapi import HTTPException, UploadFile, status

import os
 
from fastapi import HTTPException, UploadFile, status
 
from core.config import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_BATCH,
)

def validate_batch_size(files: list[UploadFile]) -> None:
    """Ensure the batch isn't empty and doesn't exceed the max file count."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were uploaded.",
        )
 
    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Too many files: received {len(files)}, "
                f"max allowed is {MAX_FILES_PER_BATCH}."
            ),
        )
 
def validate_file_type(file: UploadFile) -> None:
    """Ensure the file is a JPG/JPEG/PNG by content-type AND extension.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
 
    content_type_ok = file.content_type in ALLOWED_CONTENT_TYPES
    extension_ok = ext in ALLOWED_EXTENSIONS
 
    if not (content_type_ok or extension_ok):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type for '{file.filename}'. "
                "Only JPG, JPEG, and PNG are supported."
            ),
        )
        
def validate_file_size(file_bytes: bytes, filename: str) -> None:
    """Ensure a single file doesn't exceed the max size, after reading it.
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"'{filename}' is {size_mb:.1f} MB, which exceeds the "
                f"10 MB per-file limit."
            ),
        )
     