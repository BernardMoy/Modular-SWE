"""Black-box tests for checkpoint 3.

The CLI is always exercised in a subprocess.  In particular, these tests do
not import the application or rely on its implementation modules.
"""

import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = next(
    candidate
    for candidate in (ROOT / "implementation" / "appctl.py", ROOT / "previous_implementation" / "appctl.py")
    if candidate.exists()
)


@pytest.fixture
def run_cli(tmp_path):
    """Run the entrypoint with an isolated, explicitly selected app root."""

    def run(*args, input_text=None, tty=False, extra_env=None):
        env = os.environ.copy()
        env.update(
            {
                "APPCTL_ROOT_DIR": str(tmp_path / "app-root"),
                "PYTHONPATH": str(ENTRYPOINT.parent),
            }
        )
        if extra_env:
            env.update(extra_env)
        # A pipe is intentional for normal tests: it is the auto-colour case.
        return subprocess.run(
            [sys.executable, str(ENTRYPOINT), *args],
            input=input_text,
            text=True,
            capture_output=True,
            cwd=tmp_path,
            env=env,
        )

    return run


def test_default_output_is_table_like_and_single_item_is_vertical(run_cli):
    result = run_cli("cli", "version")

    assert result.returncode == 0
    assert result.stderr == ""
    # A one-item result must not be rendered as an unlabelled scalar.
    assert result.stdout.strip()
    assert "appctl" in result.stdout
    assert ":" in result.stdout


@pytest.mark.parametrize("format_name", ["csv", "json", "yaml", "count", "ids"])
def test_each_output_format_is_available(run_cli, format_name):
    result = run_cli(f"--format={format_name}", "cli", "version")

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    output = result.stdout.strip()
    assert output
    if format_name == "csv":
        assert list(csv.reader(io.StringIO(output)))
    elif format_name == "json":
        json.loads(output)
    elif format_name == "yaml":
        assert yaml.safe_load(output) is not None
    elif format_name == "count":
        assert re.fullmatch(r"\d+", output)
    else:
        assert re.fullmatch(r"\S+(?:\s+\S+)*", output)


def test_invalid_format_or_field_is_a_stderr_error(run_cli):
    result = run_cli("--format=table", "--field=does-not-exist", "cli", "version")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Error: Invalid field: does-not-exist." in result.stderr


def test_fields_preserve_requested_order_and_case_insensitive_lookup(run_cli):
    result = run_cli(
        "--format=csv",
        "--fields=VERSION,NAME",
        "cli",
        "version",
    )

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert len(rows) >= 1
    assert [column.casefold() for column in rows[0]] == ["version", "name"]


def test_no_color_removes_ansi_from_error(run_cli):
    result = run_cli("--no-color", "not-a-command")

    assert result.returncode == 1
    assert result.stderr.startswith("Error: ")
    assert "\x1b[" not in result.stderr


def test_color_force_colors_error_prefix(run_cli):
    result = run_cli("--color", "not-a-command")

    assert result.returncode == 1
    assert "Error:" in re.sub(r"\x1b\[[0-9;]*m", "", result.stderr)
    assert "\x1b[" in result.stderr


def test_color_config_enables_color_when_flag_is_not_present(run_cli, tmp_path):
    config = tmp_path / "color.yml"
    config.write_text("color: true\n")
    result = run_cli(
        "not-a-command",
        extra_env={"APPCTL_CONFIG_PATH": str(config)},
    )

    assert result.returncode == 1
    assert "\x1b[" in result.stderr


def test_success_message_is_stdout_and_quiet_suppresses_it(run_cli):
    normal = run_cli("site", "create", "example")
    quiet = run_cli("--quiet", "site", "create", "example")

    assert normal.returncode == 0
    assert normal.stderr == ""
    assert normal.stdout.startswith("Success: ")
    assert quiet.returncode == 0
    assert quiet.stdout == ""


def test_missing_positional_value_is_read_from_stdin(run_cli):
    result = run_cli("site", "create", input_text="example\n")

    assert result.returncode == 0
    assert "missing_positional" not in result.stderr


def test_invalid_json_stdin_fallback_reports_raw_input(run_cli):
    raw = "not valid json"
    result = run_cli("--format=json", "site", "create", input_text=raw + "\n")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"Error: Invalid JSON: {raw}\n"


def test_confirmation_accepts_trimmed_case_insensitive_yes(run_cli):
    result = run_cli("site", "delete", "example", input_text="  Y  \n")

    assert result.returncode == 0
    assert "[y/n]" in result.stdout + result.stderr
    assert "Operation cancelled" not in result.stderr


@pytest.mark.parametrize("answer", ["n", "N", " yes ", "", "maybe"])
def test_confirmation_anything_other_than_exact_y_cancels(run_cli, answer):
    result = run_cli("site", "delete", "example", input_text=answer + "\n")

    assert result.returncode == 0
    assert result.stderr == "Warning: Operation cancelled.\n"


def test_yes_bypasses_confirmation_prompt(run_cli):
    result = run_cli("--yes", "site", "delete", "example")

    assert result.returncode == 0
    assert "[y/n]" not in result.stdout + result.stderr


def test_debug_is_stderr_logged_and_has_human_readable_elapsed_seconds(run_cli, tmp_path):
    result = run_cli("--debug", "cli", "version")
    log = tmp_path / "app-root" / "logs" / "appctl.log"

    assert result.returncode == 0
    assert result.stdout
    assert result.stderr.startswith("Debug:")
    assert re.search(r"\b\d+(?:\.\d+)?s\b", result.stderr)
    assert log.exists()
    assert "Debug:" in log.read_text()


def test_invocations_are_delimited_and_log_timestamp_is_utc_parseable(run_cli, tmp_path):
    assert run_cli("cli", "version").returncode == 0
    assert run_cli("not-a-command").returncode == 1
    log = tmp_path / "app-root" / "logs" / "appctl.log"
    contents = log.read_text()

    assert contents.count("\n") >= 2
    assert contents.count("=" * 10) >= 1
    timestamp = contents.splitlines()[0]
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).utcoffset().total_seconds() == 0


def test_quiet_suppresses_informational_output_but_not_errors(run_cli):
    info = run_cli("--quiet", "cli", "version")
    error = run_cli("--quiet", "not-a-command")

    assert info.returncode == 0
    assert info.stdout == ""
    assert error.returncode == 1
    assert error.stderr.startswith("Error: ")
