"""Acceptance tests for checkpoint 1's appctl command-line contract."""

import os
import re

from .conftest import help_command_names


def test_no_arguments_prints_successful_sorted_top_level_help(run_appctl):
    result = run_appctl()

    assert result.returncode == 0
    assert result.stdout
    assert result.stderr == ""

    names = help_command_names(result.stdout)
    assert names, "help must list at least one top-level command"
    assert names == sorted(names, key=str.casefold)


def test_version_flag_is_rewritten_to_cli_version(run_appctl):
    flag = run_appctl("--version")
    explicit = run_appctl("cli", "version")

    assert flag.returncode == explicit.returncode == 0
    assert flag.stdout == explicit.stdout
    assert flag.stderr == explicit.stderr == ""


def test_command_help_flag_is_equivalent_to_help_command(run_appctl):
    listing = run_appctl()
    names = help_command_names(listing.stdout)
    command = next((name for name in names if name.casefold() not in {"help", "cli"}), None)
    if command is None:
        command = names[0]

    flag = run_appctl(command, "--help")
    explicit = run_appctl("help", command)

    assert flag.returncode == explicit.returncode == 0
    assert flag.stdout == explicit.stdout
    assert flag.stderr == explicit.stderr


def test_unknown_top_level_command_has_required_stderr_and_exit_code(run_appctl):
    result = run_appctl("definitely-not-a-registered-command")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "Error: 'definitely-not-a-registered-command' is not a registered appctl command. "
        "See 'appctl help' for available commands.\n"
    )


def test_close_unknown_top_level_command_includes_deterministic_suggestion(run_appctl):
    listing = run_appctl()
    names = help_command_names(listing.stdout)
    canonical = next(name for name in names if name.casefold() not in {"help", "cli"})
    typo = canonical[:-1] if len(canonical) > 1 else canonical + "x"
    if typo.casefold() in {name.casefold() for name in names}:
        typo += "x"

    first = run_appctl(typo)
    second = run_appctl(typo)

    assert first.returncode == second.returncode == 1
    assert first.stdout == second.stdout == ""
    expected_prefix = (
        f"Error: '{typo}' is not a registered appctl command. "
        "See 'appctl help' for available commands.\n"
    )
    assert first.stderr.startswith(expected_prefix)
    assert first.stderr == second.stderr
    assert re.search(r"Did you mean '[^']+'\?\n\Z", first.stderr)


def test_missing_subcommand_reports_parent_and_help_path(run_appctl):
    # The documented example establishes a hierarchical `site create` path.
    result = run_appctl("site", "not-a-registered-subcommand")

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(
        "Error: 'not-a-registered-subcommand' is not a registered subcommand of 'site'. "
        "See 'appctl help site' for available subcommands.\n"
    )


def test_site_create_missing_required_arguments_prints_usage_to_stdout(run_appctl):
    result = run_appctl("site", "create")

    assert result.returncode == 1
    assert result.stderr == ""
    assert re.search(r"^usage: appctl site create .+", result.stdout, re.MULTILINE)


def test_unknown_parameter_is_reported_as_a_parameter_error(run_appctl):
    result = run_appctl("cli", "version", "--not-a-declared-parameter=value")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Parameter errors:" in result.stderr
    assert "unknown --not-a-declared-parameter parameter" in result.stderr


def test_multiple_unknown_parameters_are_collected_under_one_error_header(run_appctl):
    result = run_appctl(
        "cli",
        "version",
        "--first-unknown=value",
        "--second-unknown=value",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.count("Parameter errors:") == 1
    assert "unknown --first-unknown parameter" in result.stderr
    assert "unknown --second-unknown parameter" in result.stderr


def test_empty_keyed_value_is_rejected_as_a_parameter_error(run_appctl):
    result = run_appctl("cli", "version", "--not-a-declared-parameter=")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Parameter errors:" in result.stderr
    assert "not-a-declared-parameter" in result.stderr


def test_unmatched_positional_token_is_rejected_before_version_handler_runs(run_appctl):
    result = run_appctl("cli", "version", "unexpected-positional")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Too many positional arguments: unexpected-positional" in result.stderr


def test_malformed_argument_token_is_rejected(run_appctl):
    result = run_appctl("cli", "version", "--not-a-declared-parameter:value")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Parameter errors:" in result.stderr or "Too many positional arguments" in result.stderr


def test_strict_arguments_mode_does_not_treat_post_command_flags_as_global(run_appctl):
    environment = os.environ.copy()
    environment["APPCTL_STRICT_ARGS_MODE"] = "1"
    result = run_appctl("cli", "version", "--not-a-declared-parameter=value", env=environment)

    assert result.returncode == 1
    assert "unknown --not-a-declared-parameter parameter" in result.stderr
