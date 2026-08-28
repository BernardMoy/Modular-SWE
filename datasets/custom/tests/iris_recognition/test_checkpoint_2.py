from __future__ import annotations

import re
from pathlib import Path

from ._helpers import (
    ALLOWED_SEGMENT_ISSUES,
    ANOMALY_FIELDS,
    DATASET_FIELDS,
    build_synthetic_iris_image,
    install_default_dataset,
    read_csv,
    write_corrupted_file,
    write_csv,
)


def _build_dataset(tmp_path: Path, isolated_workspace: Path) -> tuple[Path, Path, Path]:
    source_dataset = tmp_path / "source-dataset"
    valid_image = source_dataset / "001" / "L" / "S1001L01.png"
    broken_image = source_dataset / "002" / "L" / "S1002L01.png"

    build_synthetic_iris_image(valid_image)
    write_corrupted_file(broken_image)

    dataset_root = install_default_dataset(isolated_workspace, source_dataset)
    dataset_csv = dataset_root / "dataset.csv"
    write_csv(
        dataset_csv,
        DATASET_FIELDS,
        [
            {
                "subject_id": "001",
                "eye": "L",
                "image_path": "001/L/S1001L01.png",
                "width": "320",
                "height": "280",
                "format": "PNG",
                "file_size": str(valid_image.stat().st_size),
            },
            {
                "subject_id": "002",
                "eye": "L",
                "image_path": "002/L/S1002L01.png",
                "width": "320",
                "height": "280",
                "format": "PNG",
                "file_size": str(broken_image.stat().st_size),
            },
        ],
    )
    return dataset_root, dataset_csv, dataset_root / "001" / "L" / "S1001L01.png"


# Verifies that `segment` prints the required summary, writes the segmentation
# CSV for successful images, writes overlay files in dataset structure, and
# records anomalies for failed images.
def test_segment_writes_requested_outputs_and_summary(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, dataset_csv, _ = _build_dataset(tmp_path, isolated_workspace)
    output_csv = tmp_path / "out" / "segmentation.csv"
    overlay_dir = tmp_path / "out" / "overlay"
    anomalies_csv = tmp_path / "out" / "anomalies.csv"

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
    assert result.stdout.splitlines() == [
        f"Dataset: {dataset_csv}",
        "",
        "Image processed: 2",
        "Successful segmentation: 1",
        "Failed segmentation: 1",
        "",
        "Anomalies found: 1",
    ]

    fieldnames, rows = read_csv(output_csv)
    assert fieldnames == [
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
    assert len(rows) == 1
    assert rows[0]["subject_id"] == "001"
    assert rows[0]["eye"] == "L"
    assert rows[0]["image_path"] == "001/L/S1001L01.png"
    for field in (
        "pupil_x",
        "pupil_y",
        "pupil_radius",
        "iris_x",
        "iris_y",
        "iris_radius",
    ):
        int(rows[0][field])

    assert (overlay_dir / "001" / "L" / "S1001L01.png").is_file()

    anomaly_fieldnames, anomaly_rows = read_csv(anomalies_csv)
    assert anomaly_fieldnames == ANOMALY_FIELDS
    assert anomaly_rows == [
        {
            "subject_id": "002",
            "eye": "L",
            "image_path": "002/L/S1002L01.png",
            "issue": anomaly_rows[0]["issue"],
        }
    ]
    assert anomaly_rows[0]["issue"] in ALLOWED_SEGMENT_ISSUES


# Verifies that `segment` throws an error when the dataset CSV columns do not
# match the required format exactly.
def test_segment_rejects_dataset_csv_with_wrong_columns(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    (tmp_path / "empty-dataset").mkdir()
    dataset_root = install_default_dataset(
        isolated_workspace, tmp_path / "empty-dataset"
    )
    dataset_csv = dataset_root / "dataset.csv"
    write_csv(
        dataset_csv,
        ["subject_id", "eye", "image_path", "width", "height", "format"],
        [],
    )

    result = run_cli("segment", str(dataset_csv))

    assert result.returncode != 0


# Verifies that `segment-one` prints the required success summary and writes an
# overlay file when segmentation succeeds.
def test_segment_one_prints_success_summary_and_writes_overlay(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, _, image_path = _build_dataset(tmp_path, isolated_workspace)
    overlay_path = tmp_path / "segment-one-overlay.png"

    result = run_cli("segment-one", str(image_path), "--output", str(overlay_path))

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0] == f"Image: {image_path}"
    assert lines[1] == ""
    assert re.fullmatch(r"Pupil: center=\(\d+, \d+\), radius=\d+", lines[2])
    assert re.fullmatch(r"Iris: center=\(\d+, \d+\), radius=\d+", lines[3])
    assert lines[4] == ""
    assert lines[5] == "Status: success"
    assert overlay_path.is_file()


# Verifies that `segment-one` prints the required failure summary and allowed
# reason values when the image cannot be segmented.
def test_segment_one_reports_failure_for_unreadable_image(
    tmp_path: Path, run_cli
) -> None:
    broken_image = tmp_path / "broken.png"
    write_corrupted_file(broken_image)

    result = run_cli("segment-one", str(broken_image))

    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0] == f"Image: {broken_image}"
    assert lines[1] == ""
    assert lines[2] == "Status: failed"
    assert lines[3].startswith("Reason: ")
    assert lines[3].removeprefix("Reason: ") in ALLOWED_SEGMENT_ISSUES
