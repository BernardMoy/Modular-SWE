"""Daugman rubber-sheet normalization."""

import math

import numpy as np
from PIL import Image

from normalization_models import NormalizedImage
from segmentation_models import SegmentationRecord

OUTPUT_HEIGHT = 64
OUTPUT_WIDTH = 512


def sample_coordinates(
    record: SegmentationRecord, height: int = OUTPUT_HEIGHT, width: int = OUTPUT_WIDTH
):
    theta = np.arange(width, dtype=np.float64) * (2.0 * math.pi / width)
    radial = np.linspace(0.0, 1.0, height, dtype=np.float64)[:, None]
    cos_theta = np.cos(theta)[None, :]
    sin_theta = np.sin(theta)[None, :]
    pupil_x = record.pupil.center_x + record.pupil.radius * cos_theta
    pupil_y = record.pupil.center_y + record.pupil.radius * sin_theta
    iris_x = record.iris.center_x + record.iris.radius * cos_theta
    iris_y = record.iris.center_y + record.iris.radius * sin_theta
    return (
        (1.0 - radial) * pupil_x + radial * iris_x,
        (1.0 - radial) * pupil_y + radial * iris_y,
    )


def _bilinear(
    gray: np.ndarray, source_x: np.ndarray, source_y: np.ndarray
) -> np.ndarray:
    height, width = gray.shape
    x0 = np.floor(source_x).astype(np.int64)
    y0 = np.floor(source_y).astype(np.int64)
    x1 = x0 + 1
    y1 = y0 + 1
    x0c = np.clip(x0, 0, width - 1)
    x1c = np.clip(x1, 0, width - 1)
    y0c = np.clip(y0, 0, height - 1)
    y1c = np.clip(y1, 0, height - 1)
    dx = source_x - x0
    dy = source_y - y0
    top = gray[y0c, x0c] * (1.0 - dx) + gray[y0c, x1c] * dx
    bottom = gray[y1c, x0c] * (1.0 - dx) + gray[y1c, x1c] * dx
    return np.clip(top * (1.0 - dy) + bottom * dy, 0, 255)


def normalize(image: Image.Image, record: SegmentationRecord) -> NormalizedImage:
    if record.pupil.radius <= 0 or record.iris.radius <= 0:
        raise ValueError("pupil and iris radii must be positive")
    gray = np.asarray(image.convert("L"), dtype=np.float64)
    source_x, source_y = sample_coordinates(record)
    result = _bilinear(gray, source_x, source_y).round().astype(np.uint8)
    return NormalizedImage(result, record.image_path)
