import io
import secrets
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import InvalidInput

EXTENSIONS = {"JPEG": ".jpg", "PNG": ".png"}
MIN_SIDE = 100
MAX_SIDE = 8000


async def save_image(file: UploadFile) -> str:
    data = await file.read(settings.max_image_bytes + 1)
    if len(data) > settings.max_image_bytes:
        mb = settings.max_image_bytes // (1024 * 1024)
        raise InvalidInput("image", f"Image must be {mb} MB or smaller")

    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            width, height = img.size
            img.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise InvalidInput("image", "File is not a readable JPEG or PNG") from None

    if fmt not in EXTENSIONS:
        raise InvalidInput("image", "Only JPEG and PNG images are accepted")
    if min(width, height) < MIN_SIDE or max(width, height) > MAX_SIDE:
        raise InvalidInput(
            "image",
            f"Image sides must be between {MIN_SIDE} and {MAX_SIDE} pixels",
        )

    name = secrets.token_hex(16) + EXTENSIONS[fmt]
    (settings.upload_path / name).write_bytes(data)
    return name


def delete_image(name: str) -> None:
    Path(settings.upload_path / name).unlink(missing_ok=True)
