"""Validity-mask construction for normalized iris samples."""

import numpy as np

from iris_normalization import sample_coordinates
from normalization_models import NormalizedImage, ValidityMask
from segmentation_models import SegmentationRecord


def _vertical_edges(gray: np.ndarray) -> np.ndarray:
    gradient = np.abs(np.diff(gray.astype(np.float32), axis=0, prepend=gray[:1]))
    return gradient > max(18.0, float(np.percentile(gradient, 88)))


def build_mask(
    image, record: SegmentationRecord, normalized: NormalizedImage
) -> ValidityMask:
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    height, width = gray.shape
    source_x, source_y = sample_coordinates(
        record, normalized.data.shape[0], normalized.data.shape[1]
    )
    x_floor = np.floor(source_x).astype(np.int64)
    y_floor = np.floor(source_y).astype(np.int64)
    in_bounds = (
        (source_x >= 0)
        & (source_x <= width - 1)
        & (source_y >= 0)
        & (source_y <= height - 1)
    )
    safe_x = np.clip(x_floor, 0, width - 1)
    safe_y = np.clip(y_floor, 0, height - 1)
    sampled = gray[safe_y, safe_x]
    invalid = ~in_bounds | (sampled > 240.0)

    # Dark regions that are both locally exceptional and vertically edged are
    # a useful eyelash proxy, while broad dark runs at either edge model lids.
    local_mean = gray.mean(axis=1, keepdims=True)
    dark = gray < (local_mean - 25.0)
    eyelash = dark & _vertical_edges(gray)
    invalid |= eyelash[safe_y, safe_x]
    upper_lid = source_y < (0.08 * height)
    lower_lid = source_y > (0.92 * height)
    invalid |= upper_lid | lower_lid
    return ValidityMask(np.where(invalid, 0, 255).astype(np.uint8))
