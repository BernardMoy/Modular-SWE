from __future__ import annotations

import re
from pathlib import Path

from ._helpers import (
    DATASET_FIELDS,
    build_synthetic_iris_image,
    install_default_dataset,
    write_csv,
)


def _build_gallery_source(
    tmp_path: Path, isolated_workspace: Path
) -> tuple[Path, Path, Path]:
    source_dataset = tmp_path / "source-dataset"
    image_path = source_dataset / "001" / "L" / "S1001L01.png"
    build_synthetic_iris_image(image_path)

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
                "file_size": str(image_path.stat().st_size),
            }
        ],
    )
    return dataset_root, dataset_csv, dataset_root / "001" / "L" / "S1001L01.png"


# Verifies that `identify` can identify the only gallery subject when the
# gallery bins are created through the CLI pipeline from the same source image.
def test_identify_matches_the_only_gallery_subject(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, dataset_csv, image_path = _build_gallery_source(tmp_path, isolated_workspace)
    segmentation_csv = tmp_path / "segmentation.csv"
    normalized_dir = tmp_path / "normalized"
    masks_dir = tmp_path / "masks"
    encoded_dir = tmp_path / "encoded"
    encoded_masks_dir = tmp_path / "encoded-masks"

    segment_result = run_cli(
        "segment", str(dataset_csv), "--output", str(segmentation_csv)
    )
    assert segment_result.returncode == 0, segment_result.stderr
    assert "Successful segmentation: 1" in segment_result.stdout.splitlines()

    normalize_result = run_cli(
        "normalize",
        str(segmentation_csv),
        "--output-dir",
        str(normalized_dir),
        "--output-masks-dir",
        str(masks_dir),
    )
    assert normalize_result.returncode == 0, normalize_result.stderr
    assert "Successful normalization: 1" in normalize_result.stdout.splitlines()

    encode_result = run_cli(
        "encode",
        str(normalized_dir),
        str(masks_dir),
        "--output-dir",
        str(encoded_dir),
        "--output-masks-dir",
        str(encoded_masks_dir),
    )
    assert encode_result.returncode == 0, encode_result.stderr
    assert "Successfully encoded: 1" in encode_result.stdout.splitlines()

    result = run_cli(
        "identify", str(image_path), str(encoded_dir), str(encoded_masks_dir)
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0].startswith("Code: ")
    assert lines[1] == ""
    assert lines[2] == "Closest subject: 001, L"
    assert re.fullmatch(r"Hamming distance: 0(?:\.0+)?", lines[3])
    assert lines[4] == "Match: True"
    assert lines[5] == ""
    assert lines[6] == "Status: success"


# Verifies that `identify` prints the required failure summary and reason when
# the encoded gallery files are not available.
def test_identify_reports_missing_gallery_failure(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, _, image_path = _build_gallery_source(tmp_path, isolated_workspace)
    missing_encoded_dir = tmp_path / "missing-encoded"
    missing_masks_dir = tmp_path / "missing-encoded-masks"

    result = run_cli(
        "identify",
        str(image_path),
        str(missing_encoded_dir),
        str(missing_masks_dir),
    )

    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0].startswith("Code: ")
    assert lines[1] == ""
    assert lines[2] == "Status: fail"
    assert lines[3] == "Reason: files_not_found"
