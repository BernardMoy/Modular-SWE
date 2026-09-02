"""Black-box tests for checkpoint 4 archive extraction.

The entrypoint is selected at runtime so the same tests can be run against
either implementation/ or previous_implementation/.
"""

import os
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

import pytest


@pytest.fixture
def entrypoint():
    configured = os.environ.get("APPCTL_ENTRYPOINT")
    if configured:
        path = Path(configured)
    else:
        candidates = (
            Path("implementation") / "appctl.py",
            Path("previous_implementation") / "appctl.py",
        )
        path = next((candidate for candidate in candidates if candidate.exists()), None)
    if path is None or not path.is_file():
        pytest.fail("Could not locate the CLI entrypoint appctl.py")
    return path.resolve()


def run_cli(entrypoint, cwd, *arguments):
    root = Path(cwd) / ".appctl-root"
    environment = os.environ.copy()
    environment.update(
        {
            "APPCTL_ROOT_DIR": str(root),
            "APPCTL_CONFIG_PATH": str(root / "config.yml"),
            "APPCTL_STDOUT_IS_TTY": "",
        }
    )
    return subprocess.run(
        [sys.executable, str(entrypoint), *arguments],
        cwd=str(cwd),
        env=environment,
        text=True,
        capture_output=True,
    )


def make_zip(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def make_tar_gz(path, files):
    staging = path.parent / "tar-staging"
    for name, content in files.items():
        target = staging / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    with tarfile.open(path, "w:gz") as archive:
        for name in files:
            archive.add(staging / name, arcname=name)


def test_unsupported_archive_is_rejected_exactly_and_does_not_extract(entrypoint, tmp_path):
    destination = tmp_path / "destination"
    destination.mkdir()
    marker = destination / "must-remain.txt"
    marker.write_text("original")

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        "--archive=package.rar",
        f"--path={destination}",
    )

    assert result.returncode == 1
    assert result.stderr == (
        "Error: Extraction only supported for '.zip' and '.tar.gz' file types.\n"
    )
    assert marker.read_text() == "original"


def test_archive_is_validated_before_extraction_for_missing_supported_file(
    entrypoint, tmp_path
):
    destination = tmp_path / "destination"
    destination.mkdir()
    marker = destination / "must-remain.txt"
    marker.write_text("original")

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        "--archive=missing.zip",
        f"--path={destination}",
    )

    assert result.returncode != 0
    assert "unknown_parameter" not in result.stderr
    assert marker.read_text() == "original"


def test_zip_is_extracted_to_requested_destination_and_overwrites_writable_files(
    entrypoint, tmp_path
):
    archive = tmp_path / "package.zip"
    make_zip(archive, {"nested/new.txt": "new", "existing.txt": "replacement"})
    destination = tmp_path / "destination with spaces"
    destination.mkdir()
    (destination / "existing.txt").write_text("old")

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        f"--archive={archive}",
        f"--path={destination}",
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert (destination / "existing.txt").read_text() == "replacement"
    assert (destination / "nested" / "new.txt").read_text() == "new"


def test_zip_uses_current_directory_when_destination_is_omitted(entrypoint, tmp_path):
    archive = tmp_path / "package.zip"
    make_zip(archive, {"from-zip.txt": "content"})

    result = run_cli(entrypoint, tmp_path, "cli", "update", f"--archive={archive}")

    assert result.returncode == 0
    assert (tmp_path / "from-zip.txt").read_text() == "content"


def test_tar_gz_is_extracted(entrypoint, tmp_path):
    archive = tmp_path / "package.tar.gz"
    make_tar_gz(archive, {"one.txt": "one", "dir/two.txt": "two"})
    destination = tmp_path / "destination"

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        f"--archive={archive}",
        f"--path={destination}",
    )

    assert result.returncode == 0
    assert (destination / "one.txt").read_text() == "one"
    assert (destination / "dir" / "two.txt").read_text() == "two"


def test_failed_tar_gz_emits_warning_before_returning_failure(entrypoint, tmp_path):
    archive = tmp_path / "broken.tar.gz"
    archive.write_bytes(b"not a tar archive")

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        f"--archive={archive}",
        f"--path={tmp_path / 'destination'}",
    )

    assert result.returncode != 0
    assert "warning" in result.stderr.casefold()


def test_non_writable_existing_files_warn_individually_and_fail_after_extraction(
    entrypoint, tmp_path
):
    archive = tmp_path / "package.zip"
    make_zip(archive, {"locked-a.txt": "new-a", "locked-b.txt": "new-b"})
    destination = tmp_path / "destination"
    destination.mkdir()
    locked = [destination / "locked-a.txt", destination / "locked-b.txt"]
    for path in locked:
        path.write_text("old")
        path.chmod(0o444)

    # Root can write chmod(0444) files, so this behavior cannot be observed in
    # that environment.  It remains covered when the suite runs unprivileged.
    if any(os.access(path, os.W_OK) for path in locked):
        pytest.skip("filesystem user can write read-only files")

    result = run_cli(
        entrypoint,
        tmp_path,
        "cli",
        "update",
        f"--archive={archive}",
        f"--path={destination}",
    )

    assert result.returncode != 0
    for path in locked:
        relative = path.relative_to(destination).as_posix()
        assert f"Warning: Unable to copy '{relative}' to current directory." in result.stderr
        assert path.read_text() == "old"
