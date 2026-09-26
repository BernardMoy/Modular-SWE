"""Deterministic pupil and iris localization using grayscale image statistics."""

from pathlib import Path
import numpy as np
from PIL import Image
from segmentation_models import Boundary, SegmentationResult


def _circle_from_mask(mask: np.ndarray, fallback: tuple[float, float]) -> Boundary:
    ys, xs = np.nonzero(mask)
    if len(xs) < 12:
        return Boundary(fallback[0], fallback[1], 0.0)
    cx, cy = float(xs.mean()), float(ys.mean())
    radius = float(np.sqrt(len(xs) / np.pi))
    return Boundary(cx, cy, radius)


def localize(image_path: str) -> SegmentationResult:
    try:
        with Image.open(Path(image_path)) as image:
            gray = np.asarray(image.convert("L"), dtype=np.float32)
    except (OSError, ValueError, SyntaxError):
        zero = Boundary(0.0, 0.0, 0.0)
        return SegmentationResult(zero, zero, False)
    if gray.ndim != 2 or min(gray.shape) < 2:
        zero = Boundary(0.0, 0.0, 0.0)
        return SegmentationResult(zero, zero, False)
    h, w = gray.shape
    # The pupil is the compact darkest region. Restricting candidates to the
    # central 80% avoids selecting a dark border or background.
    yy, xx = np.ogrid[:h, :w]
    central = (xx > 0.1 * w) & (xx < 0.9 * w) & (yy > 0.1 * h) & (yy < 0.9 * h)
    threshold = float(np.percentile(gray[central], 12))
    pupil_mask = (gray <= threshold) & central
    pupil = _circle_from_mask(pupil_mask, (w / 2, h / 2))
    if pupil.radius <= 0:
        return SegmentationResult(pupil, Boundary(w / 2, h / 2, 0.0), False)
    # Estimate the outer edge from a radial gradient around the pupil. This
    # keeps the two circles independent while remaining entirely classical.
    angles = np.linspace(0, 2 * np.pi, 96, endpoint=False)
    candidates = []
    for angle in angles:
        max_r = min(w, h) / 2
        radii = np.arange(max(pupil.radius * 1.4, 3), max_r, 1.0)
        xs = np.clip(
            np.rint(pupil.center_x + radii * np.cos(angle)).astype(int), 0, w - 1
        )
        ys = np.clip(
            np.rint(pupil.center_y + radii * np.sin(angle)).astype(int), 0, h - 1
        )
        values = gray[ys, xs]
        if len(values) > 2:
            candidates.append(float(radii[np.argmax(np.abs(np.diff(values))) + 1]))
    iris_radius = float(np.median(candidates)) if candidates else 0.0
    iris = Boundary(pupil.center_x, pupil.center_y, iris_radius)
    return SegmentationResult(pupil, iris, iris_radius > 0)
