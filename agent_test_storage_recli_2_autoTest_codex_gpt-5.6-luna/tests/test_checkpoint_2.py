"""Black-box tests for checkpoint 2.

The CLI is always exercised in a subprocess.  Config files and working
directories are temporary, so these tests do not depend on repository data or
implementation details.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _entrypoint():
    """Use the implementation under test, with the previous version as fallback."""
    for directory in ("implementation", "previous_implementation"):
        candidate = ROOT / directory / "appctl.py"
        if candidate.is_file():
            return candidate
    pytest.fail("Could not find appctl.py under implementation/ or previous_implementation/")


def run_cli(tmp_path, *args, cwd=None, files=None, env=None):
    """Run only the public command-line entrypoint."""
    if files:
        for relative, contents in files.items():
            target = tmp_path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents)

    command_env = os.environ.copy()
    command_env.update(
        {
            "APPCTL_ROOT_DIR": str(tmp_path / "appctl-root"),
            "PYTHONPATH": str(_entrypoint().parent),
        }
    )
    if env:
        command_env.update({key: str(value) for key, value in env.items()})

    return subprocess.run(
        [sys.executable, str(_entrypoint()), *args],
        cwd=str(cwd or tmp_path),
        env=command_env,
        text=True,
        capture_output=True,
    )


def write_global_config(tmp_path, contents):
    config = tmp_path / "appctl-root" / "config" / "config.yml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(contents)
    return config


def test_disabled_command_is_rejected_with_required_diagnostic(tmp_path):
    write_global_config(tmp_path, "disabled_commands:\n  - site\n")

    result = run_cli(tmp_path, "site", "create", "example")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Error: The 'site' command has been disabled.\n"


def test_project_config_overrides_global_config(tmp_path):
    write_global_config(tmp_path, "disabled_commands: []\n")
    project = tmp_path / "workspace"
    project.mkdir()
    (project / "appctl.yml").write_text("disabled_commands:\n  - site\n")

    result = run_cli(tmp_path, "site", "create", "example", cwd=project)

    assert result.returncode == 1
    assert result.stderr == "Error: The 'site' command has been disabled.\n"


def test_local_project_config_takes_priority_over_project_config(tmp_path):
    project = tmp_path / "workspace"
    project.mkdir()
    (project / "appctl.yml").write_text("disabled_commands: []\n")
    (project / "appctl.local.yml").write_text("disabled_commands:\n  - site\n")

    result = run_cli(tmp_path, "site", "create", "example", cwd=project)

    assert result.returncode == 1
    assert result.stderr == "Error: The 'site' command has been disabled.\n"


def test_project_search_stops_at_nearest_directory_with_config(tmp_path):
    parent = tmp_path / "parent"
    child = parent / "child"
    child.mkdir(parents=True)
    (parent / "appctl.yml").write_text("disabled_commands:\n  - site\n")

    result = run_cli(tmp_path, "site", "create", "example", cwd=child)

    assert result.returncode == 1
    assert result.stderr == "Error: The 'site' command has been disabled.\n"


def test_inherited_config_is_replaced_by_derived_arrays_by_default(tmp_path):
    base = tmp_path / "base.yml"
    base.write_text("disabled_commands:\n  - cli\n")
    project = tmp_path / "workspace"
    project.mkdir()
    (project / "appctl.yml").write_text(
        "_:\n  inherit: ../base.yml\ndisabled_commands:\n  - site\n"
    )

    site_result = run_cli(tmp_path, "site", "create", "example", cwd=project)
    cli_result = run_cli(tmp_path, "cli", cwd=project)

    assert site_result.returncode == 1
    assert site_result.stderr == "Error: The 'site' command has been disabled.\n"
    assert cli_result.returncode == 0


def test_inherited_config_appends_arrays_when_merge_is_enabled(tmp_path):
    base = tmp_path / "base.yml"
    base.write_text("disabled_commands:\n  - cli\n")
    project = tmp_path / "workspace"
    project.mkdir()
    (project / "appctl.yml").write_text(
        "_:\n  inherit: ../base.yml\n  merge: true\ndisabled_commands:\n  - site\n"
    )

    cli_result = run_cli(tmp_path, "cli", cwd=project)
    site_result = run_cli(tmp_path, "site", "create", "example", cwd=project)

    assert cli_result.returncode == 1
    assert cli_result.stderr == "Error: The 'cli' command has been disabled.\n"
    assert site_result.returncode == 1
    assert site_result.stderr == "Error: The 'site' command has been disabled.\n"


def test_runtime_global_flags_are_accepted_and_override_config(tmp_path):
    write_global_config(tmp_path, "color: always\n")

    result = run_cli(
        tmp_path,
        "--color=never",
        "--debug=true",
        "--quiet=true",
        "site",
        "create",
        "example",
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_runtime_alias_overrides_file_alias(tmp_path):
    write_global_config(tmp_path, '"@deploy":\n  path: ./local\n')
    runtime_alias = json.dumps({"@deploy": ["@missing"]})

    result = run_cli(
        tmp_path,
        "@deploy",
        "site",
        "create",
        "example",
        env={"APPCTL_RUNTIME_ALIAS": runtime_alias},
    )

    assert result.returncode == 1
    assert result.stderr == (
        "Error: Group '@deploy' contains one or more invalid aliases: @missing.\n"
    )


def test_file_alias_group_lists_invalid_members_in_config_order(tmp_path):
    write_global_config(
        tmp_path,
        '"@deploy-all":\n  - "@missing-one"\n  - "@missing-two"\n',
    )

    result = run_cli(tmp_path, "@deploy-all", "site", "list")

    assert result.returncode == 1
    assert result.stderr == (
        "Error: Group '@deploy-all' contains one or more invalid aliases: "
        "@missing-one, @missing-two.\n"
    )


def test_unknown_alias_reports_exact_error_and_close_suggestion(tmp_path):
    write_global_config(tmp_path, '"@staging":\n  path: ./staging\n')

    result = run_cli(tmp_path, "@stagng", "site", "create", "example")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "Error: Alias '@stagng' not found.\nDid you mean '@staging'?\n"
    )


def test_unknown_alias_without_close_match_has_no_suggestion(tmp_path):
    result = run_cli(tmp_path, "@completely-unknown", "site", "list")

    assert result.returncode == 1
    assert result.stderr == "Error: Alias '@completely-unknown' not found.\n"


def test_all_without_registered_aliases_reports_exact_error(tmp_path):
    result = run_cli(tmp_path, "@all", "site", "list")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Error: Cannot use '@all' when no aliases are registered.\n"


def test_first_run_creates_missing_global_defaults(tmp_path):
    config = tmp_path / "appctl-root" / "config" / "config.yml"

    result = run_cli(tmp_path, "--help")

    assert result.returncode == 0
    assert config.is_file()
    contents = config.read_text()
    assert "locale: en_US" in contents
    assert "installer_version: stable" in contents


def test_existing_global_defaults_are_not_overwritten_on_first_run(tmp_path):
    config = write_global_config(
        tmp_path, "locale: fr_FR\ninstaller_version: beta\n"
    )

    result = run_cli(tmp_path, "--help")

    assert result.returncode == 0
    contents = config.read_text()
    assert "locale: fr_FR" in contents
    assert "installer_version: beta" in contents


def test_first_run_adds_only_the_missing_global_default(tmp_path):
    config = write_global_config(tmp_path, "locale: fr_FR\n")

    result = run_cli(tmp_path, "--help")

    assert result.returncode == 0
    contents = config.read_text()
    assert "locale: fr_FR" in contents
    assert "installer_version: stable" in contents


def test_explicit_global_config_path_is_used(tmp_path):
    custom_config = tmp_path / "custom" / "settings.yml"
    custom_config.parent.mkdir()
    custom_config.write_text("disabled_commands:\n  - site\n")

    result = run_cli(
        tmp_path,
        "site",
        "create",
        "example",
        env={"APPCTL_CONFIG_PATH": custom_config},
    )

    assert result.returncode == 1
    assert result.stderr == "Error: The 'site' command has been disabled.\n"
