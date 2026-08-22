from __future__ import annotations

import csv
import math
import shutil
import struct
import zlib
from pathlib import Path


DATASET_FIELDS = [
    "subject_id",
    "eye",
    "image_path",
    "width",
    "height",
    "format",
    "file_size",
]

SEGMENTATION_FIELDS = [
    "subject_id",
    "eye",
    "image_path",
    "pupil_x",
    "pupil_y",
    "pupil_radius",
    "iris_x",
    "iris_y",
    "iris_radius",
]

ANOMALY_FIELDS = ["subject_id", "eye", "image_path", "issue"]

ALLOWED_SEGMENT_ISSUES = {
    "segmentation_failed",
    "zero_radius",
    "pupil_out_of_bounds",
    "iris_out_of_bounds",
    "pupil_larger_than_iris",
}

ALLOWED_NORMALIZE_ISSUES = {"failed_normalization", "image_load_failed"}
ALLOWED_ENCODE_ISSUES = {
    "failed_to_encode",
    "image_load_failed",
    "mask_load_failed",
}
ALLOWED_IDENTIFY_ISSUES = {
    "files_not_found",
    "code_load_failed",
    "mask_load_failed",
}

NORMALIZED_WIDTH = 512
NORMALIZED_HEIGHT = 64
ENCODED_BIT_LENGTH = 3 * 4 * (NORMALIZED_HEIGHT // 8) * (NORMALIZED_WIDTH // 8) * 2
ENCODED_BYTE_LENGTH = ENCODED_BIT_LENGTH // 8

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(tag + payload) & 0xFFFFFFFF
    return (
        struct.pack("!I", len(payload))
        + tag
        + payload
        + struct.pack("!I", checksum)
    )


def write_grayscale_png(path: Path, pixels: list[list[int]]) -> None:
    if not pixels or not pixels[0]:
        raise ValueError("PNG pixel data must be non-empty.")

    width = len(pixels[0])
    if any(len(row) != width for row in pixels):
        raise ValueError("All PNG rows must have the same width.")

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        raw.extend(row)

    ihdr = struct.pack("!IIBBBBB", width, len(pixels), 8, 0, 0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _png_chunk(b"IEND", b"")
    )


def write_corrupted_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not-a-valid-image")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def read_png_size(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if payload[:8] != PNG_SIGNATURE:
        raise ValueError(f"Not a PNG file: {path}")
    width, height = struct.unpack("!II", payload[16:24])
    return width, height


def install_default_dataset(workspace_root: Path, source_dataset: Path) -> Path:
    dataset_root = workspace_root / "data" / "CASIA-Iris-Interval"
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dataset, dataset_root)
    return dataset_root


def build_synthetic_iris_image(
    path: Path,
    *,
    width: int = 320,
    height: int = 280,
    pupil: tuple[int, int, int] = (156, 142, 36),
    iris: tuple[int, int, int] = (160, 140, 96),
) -> None:
    pupil_x, pupil_y, pupil_radius = pupil
    iris_x, iris_y, iris_radius = iris

    pixels: list[list[int]] = []
    for y in range(height):
        row: list[int] = []
        for x in range(width):
            pupil_distance = math.hypot(x - pupil_x, y - pupil_y)
            iris_distance = math.hypot(x - iris_x, y - iris_y)

            value = 230
            if iris_distance <= iris_radius:
                value = 110 + ((x * 7 + y * 3) % 20)
            if iris_radius - 2 <= iris_distance <= iris_radius + 2:
                value = 185
            if pupil_distance <= pupil_radius:
                value = 15
            if pupil_radius - 1 <= pupil_distance <= pupil_radius + 1:
                value = 70
            row.append(value)
        pixels.append(row)

    write_grayscale_png(path, pixels)


def build_normalized_pattern(path: Path) -> None:
    pixels: list[list[int]] = []
    for y in range(NORMALIZED_HEIGHT):
        row = [32 + ((x * 5 + y * 11) % 192) for x in range(NORMALIZED_WIDTH)]
        pixels.append(row)
    write_grayscale_png(path, pixels)


def build_mask_png(path: Path, *, value: int) -> None:
    pixels = [[value for _ in range(NORMALIZED_WIDTH)] for _ in range(NORMALIZED_HEIGHT)]
    write_grayscale_png(path, pixels)
