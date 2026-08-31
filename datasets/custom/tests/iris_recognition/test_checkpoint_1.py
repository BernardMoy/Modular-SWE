from __future__ import annotations

import base64
import csv
import shutil
import struct
import zlib
from pathlib import Path

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5W0AAAAASUVORK5CYII="
)
JPEG_1X1 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxAQEBUQEBAVFhUVFRUVFRUVFRUVFRUVFRUXFhUVFRUYHSggGBolGxUVITEhJSkrLi4uFx8zODMsNygtLisBCgoKDg0OGhAQGi0fHyUtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAAEAAQMBEQACEQEDEQH/xAAXAAADAQAAAAAAAAAAAAAAAAAAAQMC/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEAMQAAAB6A//xAAVEAEBAAAAAAAAAAAAAAAAAAAAEf/aAAgBAQABBQJf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAwEBPwEf/8QAFBEBAAAAAAAAAAAAAAAAAAAAEP/aAAgBAgEBPwEf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQAGPwJf/8QAFBABAAAAAAAAAAAAAAAAAAAAEP/aAAgBAQABPyFf/9k="
)


def _write_png(path: Path) -> None:
    path.write_bytes(PNG_1X1)


def _write_jpeg(path: Path) -> None:
    path.write_bytes(JPEG_1X1)


def _write_corrupted_jpg(path: Path) -> None:
    path.write_bytes(b"not-a-valid-image")


def _write_invalid_format(path: Path) -> None:
    path.write_bytes(b"GIF89a")


def _write_zero_dimension_png(path: Path) -> None:
    def chunk(tag: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return (
            struct.pack("!I", len(payload))
            + tag
            + payload
            + struct.pack("!I", checksum)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!IIBBBBB", 0, 0, 8, 2, 0, 0, 0)
    path.write_bytes(
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b""))
        + chunk(b"IEND", b"")
    )


def _build_dataset(root: Path) -> Path:
    subject = root / "001"
    (subject / "L").mkdir(parents=True)
    (subject / "R").mkdir(parents=True)
    _write_png(subject / "L" / "S1001L01.png")
    _write_jpeg(subject / "L" / "S1001L02.jpg")
    _write_jpeg(subject / "R" / "S1001R01.jpeg")

    subject = root / "alpha"
    (subject / "L").mkdir(parents=True)
    _write_png(subject / "L" / "alpha-L-01.png")

    subject = root / "003"
    (subject / "R").mkdir(parents=True)
    _write_jpeg(subject / "R" / "S1003R01.jpg")

    (root / "004").mkdir(parents=True)

    subject = root / "005"
    (subject / "L").mkdir(parents=True)
    (subject / "R").mkdir(parents=True)

    subject = root / "006"
    (subject / "L").mkdir(parents=True)
    (subject / "R").mkdir(parents=True)
    _write_corrupted_jpg(subject / "L" / "broken.jpg")
    _write_invalid_format(subject / "R" / "not-an-image.gif")

    subject = root / "007"
    (subject / "L").mkdir(parents=True)
    _write_zero_dimension_png(subject / "L" / "zero.png")

    return root


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _install_default_dataset(workspace_root: Path, source_dataset: Path) -> Path:
    dataset_root = workspace_root / "data" / "CASIA-Iris-Interval"
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dataset, dataset_root)
    return dataset_root


# Verifies that `scan` prints the full summary and writes both CSV outputs
# with the expected valid-image rows and anomaly rows.
def test_scan_prints_expected_summary_and_writes_csv_outputs(
    tmp_path: Path, run_cli
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")
    output_csv = tmp_path / "out" / "dataset.csv"
    anomalies_csv = tmp_path / "out" / "anomalies.csv"

    result = run_cli(
        "scan",
        str(dataset_root),
        "--output",
        str(output_csv),
        "--anomalies",
        str(anomalies_csv),
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    output_lines = result.stdout.splitlines()
    assert output_lines[0] == f"Dataset root: {dataset_root}"
    assert "Subjects found: 7" in output_lines  # Count all subjects that simply present
    assert (
        "- Both eyes present: 1" in output_lines
    )  # 001 only - note that both must have valid entries
    assert "- Left eyes only: 1" in output_lines  # alpha
    assert "- Right eyes only: 1" in output_lines  # 003
    assert "- Neither eye present: 4" in output_lines  # 004, 005, 006, 007
    assert "Total valid images:" in output_lines
    assert "- Left: 3" in output_lines  # 001 001 alpha
    assert "- Right: 2" in output_lines  # 001 003
    assert "Anomalies found: 5" in output_lines

    dataset_rows = _read_csv(output_csv)
    assert sorted(dataset_rows, key=lambda row: row["image_path"]) == [
        {
            "subject_id": "001",
            "eye": "L",
            "image_path": "001/L/S1001L01.png",
            "width": "1",
            "height": "1",
            "format": "PNG",
            "file_size": str(len(PNG_1X1)),
        },
        {
            "subject_id": "001",
            "eye": "L",
            "image_path": "001/L/S1001L02.jpg",
            "width": "1",
            "height": "1",
            "format": "JPEG",
            "file_size": str(len(JPEG_1X1)),
        },
        {
            "subject_id": "001",
            "eye": "R",
            "image_path": "001/R/S1001R01.jpeg",
            "width": "1",
            "height": "1",
            "format": "JPEG",
            "file_size": str(len(JPEG_1X1)),
        },
        {
            "subject_id": "003",
            "eye": "R",
            "image_path": "003/R/S1003R01.jpg",
            "width": "1",
            "height": "1",
            "format": "JPEG",
            "file_size": str(len(JPEG_1X1)),
        },
        {
            "subject_id": "alpha",
            "eye": "L",
            "image_path": "alpha/L/alpha-L-01.png",
            "width": "1",
            "height": "1",
            "format": "PNG",
            "file_size": str(len(PNG_1X1)),
        },
    ]

    anomaly_rows = _read_csv(anomalies_csv)
    assert len(anomaly_rows) == 5
    assert {
        "subject_id": "004",
        "eye": "",
        "image_path": "",
        "issue": "missing_both_eyes",
    } in anomaly_rows
    assert {
        "subject_id": "005",
        "eye": "",
        "image_path": "",
        "issue": "missing_both_eyes",
    } in anomaly_rows
    assert {
        "subject_id": "006",
        "eye": "L",
        "image_path": "006/L/broken.jpg",
        "issue": "corrupted_image",
    } in anomaly_rows
    assert {
        "subject_id": "006",
        "eye": "R",
        "image_path": "006/R/not-an-image.gif",
        "issue": "invalid_format",
    } in anomaly_rows

    zero_dimension_candidates = [
        row for row in anomaly_rows if row["image_path"] == "007/L/zero.png"
    ]
    assert len(zero_dimension_candidates) == 1
    assert zero_dimension_candidates[0]["subject_id"] == "007"
    assert zero_dimension_candidates[0]["eye"] == "L"
    assert zero_dimension_candidates[0]["issue"] in {
        "zero_dimension_image",
        "corrupted_image",
    }


# Verifies that `scan` still reports counts correctly when no CSV outputs are
# requested and that invalid files do not count as valid images.
def test_scan_ignores_non_image_files_when_output_is_not_requested(
    tmp_path: Path, run_cli
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")

    result = run_cli("scan", str(dataset_root))

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    output_lines = result.stdout.splitlines()
    assert (
        "Total valid images:" in output_lines
    )  # numbers same as previous test, see above
    assert "- Left: 3" in output_lines
    assert "- Right: 2" in output_lines
    assert "Anomalies found: 5" in output_lines


# Verifies that `inspect` lists filenames for a subject that has data for both eyes.
def test_inspect_lists_images_for_existing_subject(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")
    _install_default_dataset(isolated_workspace, dataset_root)

    result = run_cli("inspect", "001")

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert (
        result.stdout
        == "\n".join(
            [
                "Subject: 001",
                "",
                "Left eye:",
                "Images: 2",
                "- S1001L01.png",
                "- S1001L02.jpg",
                "",
                "Right eye:",
                "Images: 1",
                "- S1001R01.jpeg",
            ]
        )
        + "\n"
    )


# Verifies that `inspect` accepts non-numeric subject IDs and reports a missing
# eye as `absent`.
def test_inspect_marks_absent_eyes_and_accepts_string_subject_ids(
    tmp_path: Path,
    run_cli,
    isolated_workspace: Path,
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")
    _install_default_dataset(isolated_workspace, dataset_root)

    result = run_cli("inspect", "alpha")

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert (
        result.stdout
        == "\n".join(
            [
                "Subject: alpha",
                "",
                "Left eye:",
                "Images: 1",
                "- alpha-L-01.png",
                "",
                "Right eye:",
                "absent",
            ]
        )
        + "\n"
    )


# Verifies that `inspect` treats existing-but-empty eye folders the same as
# missing eye folders.
def test_inspect_treats_empty_eye_folders_as_absent(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")
    _install_default_dataset(isolated_workspace, dataset_root)

    result = run_cli(
        "inspect", "005"
    )  # 005 has an empty L and empty R folders --> absent

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert (
        result.stdout
        == "\n".join(
            [
                "Subject: 005",
                "",
                "Left eye:",
                "absent",
                "",
                "Right eye:",
                "absent",
            ]
        )
        + "\n"
    )


# Verifies that `inspect` prints the required message for an unknown subject ID.
def test_inspect_reports_missing_subject(
    tmp_path: Path, run_cli, isolated_workspace: Path
) -> None:
    dataset_root = _build_dataset(tmp_path / "dataset")
    _install_default_dataset(isolated_workspace, dataset_root)

    result = run_cli("inspect", "does-not-exist")

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == "Subject does-not-exist is not present.\n"
