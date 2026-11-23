
import io

import pytest

from fastapi import HTTPException, UploadFile

from backend.upload_security import (
    MAX_UPLOAD_SIZE,
    validate_csv_upload,
)


def make_upload(
    content: bytes,
    filename: str = "features.csv",
):
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
    )


@pytest.mark.anyio
async def test_valid_csv_upload():
    file = make_upload(
        b"run_id,rms\nmotor_01,0.2\n"
    )

    content = await validate_csv_upload(file)

    assert content == b"run_id,rms\nmotor_01,0.2\n"


@pytest.mark.anyio
async def test_invalid_extension():
    file = make_upload(
        b"invalid",
        filename="features.exe",
    )

    with pytest.raises(HTTPException) as exc:
        await validate_csv_upload(file)

    assert exc.value.status_code == 415


@pytest.mark.anyio
async def test_empty_csv():
    file = make_upload(b"")

    with pytest.raises(HTTPException) as exc:
        await validate_csv_upload(file)

    assert exc.value.status_code == 400


@pytest.mark.anyio
async def test_oversized_csv():
    file = make_upload(
        b"a" * (MAX_UPLOAD_SIZE + 1)
    )

    with pytest.raises(HTTPException) as exc:
        await validate_csv_upload(file)

    assert exc.value.status_code == 413


@pytest.mark.anyio
async def test_null_bytes_rejected():
    file = make_upload(
        b"run_id,rms\nmotor\x00,0.2"
    )

    with pytest.raises(HTTPException) as exc:
        await validate_csv_upload(file)

    assert exc.value.status_code == 400
