"""Black-box tests for the persistent state database checkpoint.

The checkpoint specifies the database location and initialization errors, but
does not specify CLI verbs for manipulating settings or migration records.
Consequently, this suite only asserts effects observable at the CLI boundary
and on the documented persistent-store location.
"""

import os
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


@pytest.fixture
def appctl_entrypoint():
    """Use the implementation selected by the test harness.

    APPCTL_IMPLEMENTATION_DIR may point at a candidate implementation. The
    default makes the suite directly runnable against this checkpoint's
    previous implementation.
    """
    selected = os.environ.get("APPCTL_IMPLEMENTATION_DIR")
    project_root = Path(__file__).resolve().parents[1]
    implementation = (
        Path(selected) if selected else project_root / "previous_implementation"
    )
    if not implementation.is_absolute():
        implementation = project_root / implementation
    entrypoint = implementation / "appctl.py"
    if not entrypoint.is_file():
        pytest.fail("Expected CLI entrypoint was not found: {}".format(entrypoint))
    return entrypoint.resolve()


def run_cli(entrypoint, *, cwd, root=None, args=("--help",)):
    environment = os.environ.copy()
    environment.pop("APPCTL_ROOT_DIR", None)
    if root is not None:
        environment["APPCTL_ROOT_DIR"] = str(root)
    return subprocess.run(
        [sys.executable, str(entrypoint), *args],
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
    )


def sqlite_files(database_directory):
    """Return files in db/ that are SQLite databases, without assuming a name."""
    databases = []
    for candidate in database_directory.iterdir():
        if not candidate.is_file():
            continue
        try:
            # Open read-only so discovery does not turn an arbitrary file into
            # a SQLite database as a side effect of the test.
            uri = "file:{}?mode=ro".format(candidate)
            with sqlite3.connect(uri, uri=True) as connection:
                connection.execute("PRAGMA schema_version").fetchone()
        except sqlite3.DatabaseError:
            continue
        databases.append(candidate)
    return databases


def test_first_cli_access_creates_sqlite_store_under_configured_root(
    tmp_path, appctl_entrypoint
):
    root = tmp_path / "state-root"

    result = run_cli(appctl_entrypoint, cwd=tmp_path, root=root)

    assert result.returncode == 0
    database_directory = root / "db"
    assert database_directory.is_dir()
    assert sqlite_files(database_directory), "no SQLite store was created in db/"


def test_root_defaults_to_working_directory_when_not_configured(
    tmp_path, appctl_entrypoint
):
    result = run_cli(appctl_entrypoint, cwd=tmp_path)

    assert result.returncode == 0
    assert (tmp_path / "db").is_dir()
    assert sqlite_files(tmp_path / "db")


def test_existing_store_is_reused_on_later_cli_access(tmp_path, appctl_entrypoint):
    root = tmp_path / "state-root"
    first = run_cli(appctl_entrypoint, cwd=tmp_path, root=root)
    assert first.returncode == 0
    before = {path.name for path in (root / "db").iterdir() if path.is_file()}
    assert before

    second = run_cli(appctl_entrypoint, cwd=tmp_path, root=root)

    assert second.returncode == 0
    after = {path.name for path in (root / "db").iterdir() if path.is_file()}
    assert before <= after
    assert sqlite_files(root / "db")


def test_database_connection_failure_uses_required_error_contract(
    tmp_path, appctl_entrypoint
):
    # A file cannot serve as the database directory, while the root itself is
    # valid for logging and other normal application state.
    invalid_root = tmp_path / "root"
    invalid_root.mkdir()
    (invalid_root / "db").write_text("not a directory")

    result = run_cli(appctl_entrypoint, cwd=tmp_path, root=invalid_root)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(
        "Error: Unable to initialize connection to appctl sqlite database: "
    )
