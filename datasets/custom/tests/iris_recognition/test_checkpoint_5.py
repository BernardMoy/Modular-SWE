from __future__ import annotations

import re
from pathlib import Path

from ._helpers import ENCODED_BYTE_LENGTH


def _write_match_inputs(path: Path, *, code_byte: int, mask_byte: int) -> tuple[Path, Path]:
    code_path = path.with_suffix(".code.bin")
    mask_path = path.with_suffix(".mask.bin")
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_bytes(bytes([code_byte]) * ENCODED_BYTE_LENGTH)
    mask_path.write_bytes(bytes([mask_byte]) * ENCODED_BYTE_LENGTH)
    return code_path, mask_path


# Verifies that `match-one` reports a successful exact match for identical code
# and mask files and includes the required valid-bit count summary.
def test_match_one_reports_exact_match_for_identical_codes(
    tmp_path: Path, run_cli
) -> None:
    code_a, mask_a = _write_match_inputs(tmp_path / "a", code_byte=0x00, mask_byte=0xFF)
    code_b, mask_b = _write_match_inputs(tmp_path / "b", code_byte=0x00, mask_byte=0xFF)

    result = run_cli(
        "match-one",
        str(code_a),
        str(mask_a),
        str(code_b),
        str(mask_b),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0] == f"Code A: {code_a}"
    assert lines[1] == f"Code B: {code_b}"
    assert lines[2] == "Max shift: 8"
    assert lines[3] == ""
    assert re.fullmatch(r"Best shift: [+-]\d+", lines[4])
    assert re.fullmatch(r"Hamming distance: 0(?:\.0+)?", lines[5])
    assert lines[6] == "Valid bit count: 12288/12288"
    assert lines[7] == "Match: True"
    assert lines[8] == ""
    assert lines[9] == "Status: success"


# Verifies that `match-one` still succeeds for readable files and reports
# `Match: False` when the best hamming distance is above the default threshold.
def test_match_one_respects_threshold_for_non_matching_codes(
    tmp_path: Path, run_cli
) -> None:
    code_a, mask_a = _write_match_inputs(tmp_path / "a", code_byte=0x00, mask_byte=0xFF)
    code_b, mask_b = _write_match_inputs(tmp_path / "b", code_byte=0xFF, mask_byte=0xFF)

    result = run_cli(
        "match-one",
        str(code_a),
        str(mask_a),
        str(code_b),
        str(mask_b),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert lines[0] == f"Code A: {code_a}"
    assert lines[1] == f"Code B: {code_b}"
    assert lines[2] == "Max shift: 8"
    assert lines[3] == ""
    assert re.fullmatch(r"Best shift: [+-]\d+", lines[4])
    assert re.fullmatch(r"Hamming distance: 1(?:\.0+)?", lines[5])
    assert lines[6] == "Valid bit count: 12288/12288"
    assert lines[7] == "Match: False"
    assert lines[8] == ""
    assert lines[9] == "Status: success"


# Verifies that `match-one` prints the required failure summary and reason when
# any of the input files are missing.
def test_match_one_reports_missing_file_failure(tmp_path: Path, run_cli) -> None:
    missing_code_a = tmp_path / "missing-a.bin"
    missing_mask_a = tmp_path / "missing-a-mask.bin"
    missing_code_b = tmp_path / "missing-b.bin"
    missing_mask_b = tmp_path / "missing-b-mask.bin"

    result = run_cli(
        "match-one",
        str(missing_code_a),
        str(missing_mask_a),
        str(missing_code_b),
        str(missing_mask_b),
    )

    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        f"Code A: {missing_code_a}",
        f"Code B: {missing_code_b}",
        "Max shift: 8",
        "",
        "Status: failed",
        "Reason: files_not_found",
    ]
