"""Black-box tests for checkpoint 4's CLI contract.

The implementation is deliberately invoked as a subprocess.  This keeps the
tests independent of the implementation's modules, classes, and function
signatures.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_DIR = next(
    (PROJECT_ROOT / name for name in ("implementation", "previous_implementation") if (PROJECT_ROOT / name).is_dir()),
    PROJECT_ROOT / "previous_implementation",
)
ENTRYPOINT = IMPLEMENTATION_DIR / "code_search.py"


def run_search(tmp_path, files, rules, *flags):
    """Create an isolated tree and return the completed CLI process."""
    root = tmp_path / "repo"
    root.mkdir()
    for relative, contents in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            str(root),
            "--rules",
            str(rules_path),
            *flags,
        ],
        cwd=ENTRYPOINT.parent,
        text=True,
        capture_output=True,
        check=False,
    )


def records(process):
    assert process.returncode == 0, process.stderr
    return [json.loads(line) for line in process.stdout.splitlines()]


def matches_and_fixes(process):
    output = records(process)
    return output, [item for item in output if item.get("event") == "fix"]


def test_fix_rule_without_mode_only_emits_matches_and_does_not_write(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "print('old')\n"},
        [
            {
                "id": "rename-print",
                "kind": "pattern",
                "languages": ["python"],
                "pattern": "print($VALUE)",
                "fix": {"kind": "replace", "template": "logger.info($VALUE)"},
            }
        ],
    )

    output = records(process)
    assert len(output) == 1
    assert output[0]["rule_id"] == "rename-print"
    assert "event" not in output[0]
    assert (tmp_path / "repo" / "main.py").read_text() == "print('old')\n"


def test_dry_run_emits_preview_and_preserves_file(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "print('old')\n"},
        [{"id": "r", "kind": "exact", "pattern": "old", "fix": {"kind": "replace", "template": "new"}}],
        "--dry-run",
    )

    output, fixes = matches_and_fixes(process)
    assert [item.get("event") for item in output] == [None, "fix"]
    assert fixes == [
        {
            "event": "fix",
            "rule_id": "r",
            "file": "main.py",
            "language": "python",
            "start": {"line": 1, "col": 8},
            "end": {"line": 1, "col": 11},
            "replacement": "new",
            "applied": False,
            "skipped_reason": None,
        }
    ]
    assert (tmp_path / "repo" / "main.py").read_text() == "print('old')\n"


def test_apply_fixes_writes_changes_and_marks_each_fix_applied(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "one old\ntwo old\n"},
        [{"id": "r", "kind": "exact", "pattern": "old", "fix": {"kind": "replace", "template": "new"}}],
        "--apply-fixes",
    )

    _output, fixes = matches_and_fixes(process)
    assert [fix["applied"] for fix in fixes] == [True, True]
    assert all(fix["skipped_reason"] is None for fix in fixes)
    assert (tmp_path / "repo" / "main.py").read_text() == "one new\ntwo new\n"


def test_mode_flags_are_mutually_exclusive_and_do_not_write(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "old\n"},
        [{"id": "r", "kind": "exact", "pattern": "old", "fix": {"kind": "replace", "template": "new"}}],
        "--dry-run",
        "--apply-fixes",
    )

    assert process.returncode != 0
    assert process.stdout == ""
    assert (tmp_path / "repo" / "main.py").read_text() == "old\n"


def test_pattern_template_supports_match_literal_dollar_and_utf8(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "wrap( café )\n"},
        [{"id": "r", "kind": "pattern", "pattern": "wrap($VALUE)", "fix": {"kind": "replace", "template": "$MATCH => $$ $VALUE"}}],
        "--dry-run",
    )

    _output, fixes = matches_and_fixes(process)
    assert fixes[0]["replacement"] == "wrap( café ) => $ café"


def test_regex_fix_has_no_captures_and_replaces_full_regex_match(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "id=123\n"},
        [{"id": "digits", "kind": "regex", "pattern": r"\d+", "fix": {"kind": "replace", "template": "0"}}],
        "--dry-run",
    )

    output, fixes = matches_and_fixes(process)
    assert output[0]["match"] == "123"
    assert "captures" not in output[0]
    assert fixes[0]["replacement"] == "0"


def test_repeated_pattern_capture_uses_text_of_first_occurrence(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "pair(value, value)\n"},
        [{"id": "r", "kind": "pattern", "pattern": "pair($X, $X)", "fix": {"kind": "replace", "template": "same($X)"}}],
        "--dry-run",
    )

    output, fixes = matches_and_fixes(process)
    assert output[0]["captures"]["$X"]["text"] == "value"
    assert len(output[0]["captures"]["$X"]["ranges"]) == 2
    assert fixes[0]["replacement"] == "same(value)"


def test_pattern_capture_keys_are_serialized_lexicographically(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "pair(first, second)\n"},
        [{"id": "r", "kind": "pattern", "pattern": "pair($B, $A)"}],
    )

    output = records(process)
    assert list(output[0]["captures"]) == ["$A", "$B"]


def test_selector_matches_requested_nodes_without_captures(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "def run():\n    return 42\n"},
        [{"id": "returns", "kind": "selector", "selector": "return_statement", "languages": ["python"]}],
    )

    output = records(process)
    assert len(output) == 1
    assert output[0]["rule_id"] == "returns"
    assert output[0]["match"] == "return 42"
    assert "captures" not in output[0]


def test_selector_fix_uses_full_node_text_as_match(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "def run():\n    return 42\n"},
        [{"id": "returns", "kind": "selector", "selector": "return_statement", "fix": {"kind": "replace", "template": "$MATCH # changed"}}],
        "--dry-run",
    )

    output, fixes = matches_and_fixes(process)
    assert output[0]["match"] == "return 42"
    assert fixes[0]["replacement"] == "return 42 # changed"
    assert "captures" not in output[0]


def test_selector_default_languages_and_language_filter(tmp_path):
    process = run_search(
        tmp_path,
        {"a.py": "value = 1\n", "b.js": "const value = 1;\n", "c.cpp": "int value = 1;\n"},
        [
            {"id": "all-programs", "kind": "selector", "selector": "program"},
            {"id": "python-only", "kind": "selector", "selector": "program", "languages": ["python"]},
        ],
    )

    output = records(process)
    assert {item["file"] for item in output if item["rule_id"] == "all-programs"} == {"a.py", "b.js", "c.cpp"}
    assert [item["file"] for item in output if item["rule_id"] == "python-only"] == ["a.py"]


def test_overlapping_apply_fixes_keep_earlier_fix_and_report_skipped_candidate(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "abc\n"},
        [
            {"id": "whole", "kind": "exact", "pattern": "abc", "fix": {"kind": "replace", "template": "X"}},
            {"id": "suffix", "kind": "exact", "pattern": "bc", "fix": {"kind": "replace", "template": "Y"}},
        ],
        "--apply-fixes",
    )

    _output, fixes = matches_and_fixes(process)
    by_rule = {fix["rule_id"]: fix for fix in fixes}
    assert by_rule["whole"]["applied"] is True
    assert by_rule["suffix"]["applied"] is False
    assert by_rule["suffix"]["skipped_reason"] == "overlap"
    assert (tmp_path / "repo" / "main.py").read_text() == "X\n"


def test_dry_run_reports_all_fix_candidates_even_when_ranges_overlap(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "abc\n"},
        [
            {"id": "whole", "kind": "exact", "pattern": "abc", "fix": {"kind": "replace", "template": "X"}},
            {"id": "suffix", "kind": "exact", "pattern": "bc", "fix": {"kind": "replace", "template": "Y"}},
        ],
        "--dry-run",
    )

    _output, fixes = matches_and_fixes(process)
    assert {fix["rule_id"] for fix in fixes} == {"whole", "suffix"}
    assert all(fix["applied"] is False and fix["skipped_reason"] is None for fix in fixes)


def test_output_is_globally_sorted_by_file_position_rule_then_match_before_fix(tmp_path):
    process = run_search(
        tmp_path,
        {"z.py": "old\n", "nested/a.py": "old\n"},
        [
            {"id": "z-rule", "kind": "exact", "pattern": "old", "fix": {"kind": "replace", "template": "z"}},
            {"id": "a-rule", "kind": "exact", "pattern": "old", "fix": {"kind": "replace", "template": "a"}},
        ],
        "--dry-run",
    )

    output = records(process)
    keys = [(item["file"], item["start"]["line"], item["start"]["col"], item["rule_id"], item.get("event") == "fix") for item in output]
    assert keys == sorted(keys, key=lambda key: (*key[:4], key[4]))
    for index in range(0, len(output), 4):
        assert output[index].get("event") is None
        assert output[index + 1].get("event") == "fix"


@pytest.mark.parametrize(
    "rule",
    [
        {"id": "s", "kind": "selector", "selector": "not_a_node"},
        {"id": "s", "kind": "selector", "selector": "return_statement", "fix": {"kind": "edit", "template": "x"}},
        {"id": "s", "kind": "selector", "selector": "return_statement", "fix": {"kind": "replace", "template": 1}},
        {"id": "s", "kind": "selector", "selector": "return_statement", "fix": {"kind": "replace"}},
        {"id": "s", "kind": "selector", "selector": "return_statement", "fix": "replace"},
    ],
)
def test_invalid_selector_or_fix_schema_is_a_cli_error(tmp_path, rule):
    process = run_search(tmp_path, {"main.py": "return 1\n"}, [rule])
    assert process.returncode == 2
    assert process.stdout == ""


def test_empty_fix_template_is_valid_and_can_delete_match(tmp_path):
    process = run_search(
        tmp_path,
        {"main.py": "remove me\n"},
        [{"id": "delete", "kind": "exact", "pattern": "remove ", "fix": {"kind": "replace", "template": ""}}],
        "--apply-fixes",
    )

    _output, fixes = matches_and_fixes(process)
    assert fixes[0]["replacement"] == ""
    assert fixes[0]["applied"] is True
    assert (tmp_path / "repo" / "main.py").read_text() == "me\n"
