from __future__ import annotations

import csv
import re
import struct
import zlib
from pathlib import Path


ALLOWED_FAILURE_REASONS = {
    "segmentation_failed",
    "zero_radius",
    "pupil_out_of_bounds",
    "iris_out_of_bounds",
    "pupil_larger_than_iris",
}


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(tag + payload) & 0xFFFFFFFF
    return (
        struct.pack("!I", len(payload))
        + tag
        + payload
        + struct.pack("!I", checksum)
    )


def _write_grayscale_png(
    path: Path,
    width: int,
    height: int,
    pixel_at: callable,
) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.append(pixel_at(x, y))

    ihdr = struct.pack("!IIBBBBB", width, height, 8, 0, 0, 0, 0)
    image_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(image_bytes)


def _write_segmentable_iris_png(path: Path) -> None:
    width = 320
    height = 280
    center_x = 160
    center_y = 140
    pupil_radius = 32
    iris_radius = 96

    def pixel_at(x: int, y: int) -> int:
        dx = x - center_x
        dy = y - center_y
        distance_sq = dx * dx + dy * dy
        if distance_sq <= pupil_radius * pupil_radius:
            return 18
        if distance_sq <= iris_radius * iris_radius:
            return 118
        return 228

    _write_grayscale_png(path, width, height, pixel_at)


def _write_corrupted_jpg(path: Path) -> None:
    path.write_bytes(b"not-a-valid-jpeg")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_dataset_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "subject_id",
        "eye",
        "image_path",
        "width",
        "height",
        "format",
        "file_size",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_segmentation_fixture(root: Path) -> tuple[Path, Path, Path]:
    dataset_root = root / "dataset"
    success_image = dataset_root / "001" / "L" / "S1001L01.png"
    broken_image = dataset_root / "alpha" / "R" / "broken.jpg"
    success_image.parent.mkdir(parents=True)
    broken_image.parent.mkdir(parents=True)

    _write_segmentable_iris_png(success_image)
    _write_corrupted_jpg(broken_image)

    dataset_csv = dataset_root / "dataset.csv"
    _write_dataset_csv(
        dataset_csv,
        [
            {
                "subject_id": "001",
                "eye": "L",
                "image_path": "001/L/S1001L01.png",
                "width": "320",
                "height": "280",
                "format": "PNG",
                "file_size": str(success_image.stat().st_size),
            },
            {
                "subject_id": "alpha",
                "eye": "R",
                "image_path": "alpha/R/broken.jpg",
                "width": "320",
                "height": "280",
                "format": "JPEG",
                "file_size": str(broken_image.stat().st_size),
            },
        ],
    )
    return dataset_csv, success_image, broken_image


# Verifies that `segment` rejects dataset CSV files whose columns do not
# exactly match the required checkpoint schema.
def test_segment_rejects_dataset_csv_with_wrong_columns(
    tmp_path: Path, run_cli
) -> None:
    dataset_csv, _, _ = _build_segmentation_fixture(tmp_path)
    invalid_csv = tmp_path / "dataset" / "invalid.csv"
    invalid_csv.write_text(
        "subject_id,eye,image_path,width,height,format\n"
        "001,L,001/L/S1001L01.png,320,280,PNG\n",
        encoding="utf-8",
    )

    result = run_cli("segment", str(invalid_csv))

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr != ""


# Verifies that `segment` prints the required summary and writes successful
# segmentation rows, anomaly rows, and overlays for successful images only.
def test_segment_prints_summary_and_writes_csvs_and_overlays(
    tmp_path: Path, run_cli
) -> None:
    dataset_csv, success_image, _ = _build_segmentation_fixture(tmp_path)
    output_csv = tmp_path / "out" / "segmentation.csv"
    anomalies_csv = tmp_path / "out" / "anomalies.csv"
    overlay_dir = tmp_path / "out" / "overlay"

    result = run_cli(
        "segment",
        str(dataset_csv),
        "--output",
        str(output_csv),
        "--overlay",
        str(overlay_dir),
        "--anomalies",
        str(anomalies_csv),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == "\n".join(
        [
            f"Dataset: {dataset_csv}",
            "",
            "Image processed: 2",
            "Successful segmentation: 1",
            "Failed segmentation: 1",
            "",
            "Anomalies found: 1",
        ]
    ) + "\n"

    segmentation_rows = _read_csv(output_csv)
    assert len(segmentation_rows) == 1
    row = segmentation_rows[0]
    assert row["subject_id"] == "001"
    assert row["eye"] == "L"
    assert row["image_path"] == "001/L/S1001L01.png"

    pupil_x = int(row["pupil_x"])
    pupil_y = int(row["pupil_y"])
    pupil_radius = int(row["pupil_radius"])
    iris_x = int(row["iris_x"])
    iris_y = int(row["iris_y"])
    iris_radius = int(row["iris_radius"])
    assert 0 <= pupil_x < 320
    assert 0 <= pupil_y < 280
    assert 0 <= iris_x < 320
    assert 0 <= iris_y < 280
    assert pupil_radius > 0
    assert iris_radius > 0
    assert pupil_radius < iris_radius

    anomaly_rows = _read_csv(anomalies_csv)
    assert anomaly_rows == [
        {
            "subject_id": "alpha",
            "eye": "R",
            "image_path": "alpha/R/broken.jpg",
            "issue": "segmentation_failed",
        }
    ]

    overlay_path = overlay_dir / "001" / "L" / "S1001L01.png"
    assert overlay_path.is_file()
    assert overlay_path.stat().st_size > 0
    assert overlay_path.read_bytes() != success_image.read_bytes()
    assert not (overlay_dir / "alpha" / "R" / "broken.jpg").exists()


# Verifies that `segment-one` reports a successful segmentation in the
# required format and writes the requested overlay image.
def test_segment_one_prints_success_summary_and_writes_overlay(
    tmp_path: Path, run_cli
) -> None:
    _, success_image, _ = _build_segmentation_fixture(tmp_path)
    overlay_path = tmp_path / "one-overlay.png"

    result = run_cli(
        "segment-one",
        str(success_image),
        "--output",
        str(overlay_path),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""

    match = re.fullmatch(
        (
            rf"Image: {re.escape(str(success_image))}\n\n"
            r"Pupil: center=\((\d+), (\d+)\), radius=(\d+)\n"
            r"Iris: center=\((\d+), (\d+)\), radius=(\d+)\n\n"
            r"Status: success\n"
        ),
        result.stdout,
    )
    assert match is not None

    pupil_x, pupil_y, pupil_radius, iris_x, iris_y, iris_radius = (
        int(group) for group in match.groups()
    )
    assert 0 <= pupil_x < 320
    assert 0 <= pupil_y < 280
    assert 0 <= iris_x < 320
    assert 0 <= iris_y < 280
    assert pupil_radius > 0
    assert iris_radius > 0
    assert pupil_radius < iris_radius

    assert overlay_path.is_file()
    assert overlay_path.stat().st_size > 0
    assert overlay_path.read_bytes() != success_image.read_bytes()


# Verifies that `segment-one` reports failure using one of the allowed
# anomaly reasons and does not create an overlay for unreadable images.
def test_segment_one_prints_failure_summary_for_unreadable_image(
    tmp_path: Path, run_cli
) -> None:
    _, _, broken_image = _build_segmentation_fixture(tmp_path)
    overlay_path = tmp_path / "broken-overlay.png"

    result = run_cli(
        "segment-one",
        str(broken_image),
        "--output",
        str(overlay_path),
    )

    assert result.stderr == ""

    match = re.fullmatch(
        (
            rf"Image: {re.escape(str(broken_image))}\n\n"
            r"Status: failed\n"
            r"Reason: ([a-z_]+)\n"
        ),
        result.stdout,
    )
    assert match is not None
    assert match.group(1) in ALLOWED_FAILURE_REASONS
    assert not overlay_path.exists()
