
from fastapi import HTTPException, UploadFile, status

MAX_UPLOAD_SIZE = 5 * 1024 * 1024
FEATURE_UPLOAD_LIMIT = 2 * 1024 * 1024


async def validate_csv_upload(
    file: UploadFile,
    max_size: int = MAX_UPLOAD_SIZE,
) -> bytes:
    """
    Validate CSV uploads using bounded reads.

    Returns file bytes after validation.
    """

    filename = file.filename or ""

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only CSV files are supported.",
        )

    if max_size <= 0:
        raise ValueError("Maximum upload size must be positive.")

    chunks = []
    total_size = 0

    while True:
        chunk = await file.read(
            min(64 * 1024, max_size - total_size + 1)
        )

        if not chunk:
            break

        total_size += len(chunk)

        if total_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="CSV file exceeds the permitted size limit.",
            )

        chunks.append(chunk)

    content = b"".join(chunks)

    if not content or not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty.",
        )

    if b"\x00" in content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file content.",
        )

    return content
