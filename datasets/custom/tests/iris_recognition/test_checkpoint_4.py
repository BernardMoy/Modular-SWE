from __future__ import annotations

from pathlib import Path

from ._helpers import (
    ALLOWED_ENCODE_ISSUES,
    ANOMALY_FIELDS,
    ENCODED_BYTE_LENGTH,
    build_mask_png,
    build_normalized_pattern,
    read_csv,
    write_corrupted_file,
)


def _build_encoded_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    normalized_dir = tmp_path / "normalized"
    masks_dir = tmp_path / "masks"

    valid_normalized = normalized_dir / "001" / "L" / "S1001L01.png"
    valid_mask = masks_dir / "001" / "L" / "S1001L01.png"
    broken_mask = masks_dir / "002" / "L" / "S1002L01.png"
    other_normalized = normalized_dir / "002" / "L" / "S1002L01.png"

    build_normalized_pattern(valid_normalized)
    build_mask_png(valid_mask, value=255)
    build_normalized_pattern(other_normalized)
    write_corrupted_file(broken_mask)

    return normalized_dir, masks_dir, valid_normalized, valid_mask


# Verifies that `encode` prints the required summary, writes code and mask bin
# files in dataset structure, and records anomalies for failed inputs.
def test_encode_writes_requested_outputs_and_summary(
    tmp_path: Path, run_cli
) -> None:
    normalized_dir, masks_dir, _, _ = _build_encoded_inputs(tmp_path)
    output_dir = tmp_path / "encoded"
    output_masks_dir = tmp_path / "encoded-masks"
    anomalies_csv = tmp_path / "anomalies.csv"

    result = run_cli(
        "encode",
        str(normalized_dir),
        str(masks_dir),
        "--output-dir",
        str(output_dir),
        "--output-masks-dir",
        str(output_masks_dir),
        "--anomalies",
        str(anomalies_csv),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Normalized input: {normalized_dir}",
        "",
        "Image processed: 2",
        "Successfully encoded: 1",
        "Failed to encode: 1",
        "",
        "Anomalies found: 1",
    ]

    code_path = output_dir / "001" / "L" / "S1001L01.bin"
    mask_path = output_masks_dir / "001" / "L" / "S1001L01.bin"
    assert code_path.is_file()
    assert mask_path.is_file()
    assert code_path.stat().st_size == ENCODED_BYTE_LENGTH
    assert mask_path.stat().st_size == ENCODED_BYTE_LENGTH
    assert mask_path.read_bytes() == b"\xff" * ENCODED_BYTE_LENGTH

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
    assert anomaly_rows[0]["issue"] in ALLOWED_ENCODE_ISSUES


# Verifies that `encode-one` prints the required success summary and writes the
# code and mask bin files using the required bit-packed output size.
def test_encode_one_prints_success_summary_and_writes_outputs(
    tmp_path: Path, run_cli
) -> None:
    _, _, normalized_image, mask_image = _build_encoded_inputs(tmp_path)
    output_code = tmp_path / "code.bin"
    output_mask = tmp_path / "mask.bin"

    result = run_cli(
        "encode-one",
        str(normalized_image),
        str(mask_image),
        "--output",
        str(output_code),
        "--output-mask",
        str(output_mask),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Image: {normalized_image}",
        f"Mask: {mask_image}",
        "Status: success",
        f"Saved to: {output_code}",
        f"Mask saved to: {output_mask}",
    ]
    assert output_code.stat().st_size == ENCODED_BYTE_LENGTH
    assert output_mask.stat().st_size == ENCODED_BYTE_LENGTH
    assert output_mask.read_bytes() == b"\xff" * ENCODED_BYTE_LENGTH


# Verifies that `encode-one` prints the required failure summary and allowed
# reason values when the mask image cannot be loaded.
def test_encode_one_reports_failure_for_unreadable_mask(
    tmp_path: Path, run_cli
) -> None:
    normalized_image = tmp_path / "normalized.png"
    broken_mask = tmp_path / "broken-mask.png"
    build_normalized_pattern(normalized_image)
    write_corrupted_file(broken_mask)

    result = run_cli("encode-one", str(normalized_image), str(broken_mask))

    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Image: {normalized_image}",
        f"Mask: {broken_mask}",
        "Status: failed",
        f"Reason: {result.stdout.splitlines()[-1].removeprefix('Reason: ')}",
    ]
    assert result.stdout.splitlines()[-1].removeprefix("Reason: ") in ALLOWED_ENCODE_ISSUES
