"""Persistence for normalized images and validity masks."""

from pathlib import Path

from PIL import Image

from normalization_models import (
    DatasetDirectoryDestination,
    NormalizationDestination,
    NormalizedResult,
    SavedNormalizationPaths,
    SingleImageDestination,
)


def _png(array, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array).save(path, format="PNG")


def write_result(
    result: NormalizedResult, destination: NormalizationDestination
) -> SavedNormalizationPaths:
    if result.image.data.shape[:2] != result.mask.data.shape[:2]:
        raise ValueError("normalized image and mask dimensions must match")
    relative = Path(result.relative_image_path)
    if isinstance(destination, DatasetDirectoryDestination):
        image_path = Path(destination.image_directory) / relative.with_suffix(".png")
        mask_path = (
            Path(destination.mask_directory) / relative.with_suffix(".png")
            if destination.mask_directory
            else None
        )
    elif isinstance(destination, SingleImageDestination):
        image_path = Path(destination.image_path)
        mask_path = Path(destination.mask_path) if destination.mask_path else None
    else:
        raise ValueError("unsupported normalization destination")
    _png(result.image.data, image_path)
    if mask_path is not None:
        _png(result.mask.data, mask_path)
    return SavedNormalizationPaths(
        str(image_path), str(mask_path) if mask_path else None
    )
