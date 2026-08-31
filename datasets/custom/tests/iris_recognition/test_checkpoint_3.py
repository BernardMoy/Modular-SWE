from __future__ import annotations

from pathlib import Path

from ._helpers import (
    ALLOWED_NORMALIZE_ISSUES,
    ANOMALY_FIELDS,
    NORMALIZED_HEIGHT,
    NORMALIZED_WIDTH,
    SEGMENTATION_FIELDS,
    build_synthetic_iris_image,
    install_default_dataset,
    read_csv,
    read_png_size,
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
    segmentation_csv = dataset_root / "segmentation.csv"
    write_csv(
        segmentation_csv,
        SEGMENTATION_FIELDS,
        [
            {
                "subject_id": "001",
                "eye": "L",
                "image_path": "001/L/S1001L01.png",
                "pupil_x": "156",
                "pupil_y": "142",
                "pupil_radius": "36",
                "iris_x": "160",
                "iris_y": "140",
                "iris_radius": "96",
            },
            {
                "subject_id": "002",
                "eye": "L",
                "image_path": "002/L/S1002L01.png",
                "pupil_x": "156",
                "pupil_y": "142",
                "pupil_radius": "36",
                "iris_x": "160",
                "iris_y": "140",
                "iris_radius": "96",
            },
        ],
    )
    return dataset_root, segmentation_csv, dataset_root / "001" / "L" / "S1001L01.png"


# Verifies that `normalize` prints the required summary, writes normalized PNGs
# and mask PNGs in dataset structure, and records anomalies for failed images.
def test_normalize_writes_requested_outputs_and_summary(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, segmentation_csv, _ = _build_dataset(tmp_path, isolated_workspace)
    output_dir = tmp_path / "normalized"
    masks_dir = tmp_path / "masks"
    anomalies_csv = tmp_path / "anomalies.csv"

    result = run_cli(
        "normalize",
        str(segmentation_csv),
        "--output-dir",
        str(output_dir),
        "--output-masks-dir",
        str(masks_dir),
        "--anomalies",
        str(anomalies_csv),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Segmentation data: {segmentation_csv}",
        "",
        "Image processed: 2",
        "Successful normalization: 1",
        "Failed normalization: 1",
        "",
        "Anomalies found: 1",
    ]

    normalized_path = output_dir / "001" / "L" / "S1001L01.png"
    mask_path = masks_dir / "001" / "L" / "S1001L01.png"
    assert normalized_path.is_file()
    assert mask_path.is_file()
    assert read_png_size(normalized_path) == (NORMALIZED_WIDTH, NORMALIZED_HEIGHT)
    assert read_png_size(mask_path) == (NORMALIZED_WIDTH, NORMALIZED_HEIGHT)

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
    assert anomaly_rows[0]["issue"] in ALLOWED_NORMALIZE_ISSUES


# Verifies that `normalize` throws an error when the segmentation CSV columns
# do not match the required format exactly.
def test_normalize_rejects_segmentation_csv_with_wrong_columns(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    (tmp_path / "empty-dataset").mkdir()
    dataset_root = install_default_dataset(
        isolated_workspace, tmp_path / "empty-dataset"
    )
    segmentation_csv = dataset_root / "segmentation.csv"
    write_csv(
        segmentation_csv,
        ["subject_id", "eye", "image_path", "pupil_x", "pupil_y", "pupil_radius"],
        [],
    )

    result = run_cli("normalize", str(segmentation_csv))

    assert result.returncode != 0


# Verifies that `normalize-one` prints the required success summary and writes
# both the normalized PNG and mask PNG in the default output dimensions.
def test_normalize_one_prints_success_summary_and_writes_outputs(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    _, _, image_path = _build_dataset(tmp_path, isolated_workspace)
    output_path = tmp_path / "normalized-one.png"
    mask_path = tmp_path / "normalized-one-mask.png"

    result = run_cli(
        "normalize-one",
        str(image_path),
        "--pupil",
        "156,142,36",
        "--iris",
        "160,140,96",
        "--output",
        str(output_path),
        "--output-mask",
        str(mask_path),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Image: {image_path}",
        "",
        "Pupil: center=(156, 142), radius=36",
        "Iris: center=(160, 140), radius=96",
        "",
        "Status: success",
        f"Saved image to: {output_path}",
        f"Saved mask to: {mask_path}",
    ]
    assert read_png_size(output_path) == (NORMALIZED_WIDTH, NORMALIZED_HEIGHT)
    assert read_png_size(mask_path) == (NORMALIZED_WIDTH, NORMALIZED_HEIGHT)


# Verifies that `normalize-one` prints the required failure summary and allowed
# reason values when the image cannot be normalized.
def test_normalize_one_reports_failure_for_unreadable_image(
    tmp_path: Path, run_cli
) -> None:
    broken_image = tmp_path / "broken.png"
    write_corrupted_file(broken_image)

    result = run_cli(
        "normalize-one",
        str(broken_image),
        "--pupil",
        "156,142,36",
        "--iris",
        "160,140,96",
    )

    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Image: {broken_image}",
        "",
        "Status: failed",
        f"Reason: {result.stdout.splitlines()[-1].removeprefix('Reason: ')}",
    ]
    assert (
        result.stdout.splitlines()[-1].removeprefix("Reason: ")
        in ALLOWED_NORMALIZE_ISSUES
    )
