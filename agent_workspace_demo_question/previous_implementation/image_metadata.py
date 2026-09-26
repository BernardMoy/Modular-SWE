"""Image metadata extraction and validation."""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class ImageMetadataResult:
    is_valid: bool
    width: int | None
    height: int | None
    format: str | None
    file_size: int
    issue: str | None


def read_metadata(image_path: str) -> ImageMetadataResult:
    """Read metadata for one file, returning a non-throwing anomaly result."""
    path = Path(image_path)
    try:
        file_size = path.stat().st_size
    except OSError:
        file_size = 0

    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return ImageMetadataResult(False, None, None, None, file_size, "invalid_format")

    try:
        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format
            # verify() catches truncated/corrupt data without retaining pixels.
            image.verify()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        return ImageMetadataResult(
            False, None, None, None, file_size, "corrupted_image"
        )

    if width == 0 and height == 0:
        return ImageMetadataResult(
            False, width, height, image_format, file_size, "zero_dimension_image"
        )
    return ImageMetadataResult(True, width, height, image_format, file_size, None)
