"""Black-box tests for the code_search command-line interface."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PROJECT_ROOT / "implementation" / "code_search.py"


def run_search(root_dir, rules, *extra_args):
    rules_file = Path(root_dir) / "rules.json"
    rules_file.write_text(json.dumps(rules), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), str(root_dir), "--rules", str(rules_file), *extra_args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result


def output_objects(result):
    assert result.stdout == "" or result.stdout.endswith("\n")
    return [json.loads(line) for line in result.stdout.splitlines()]


def match(rule_id, file, start_line, start_col, end_line, end_col, value):
    return {
        "rule_id": rule_id,
        "file": file,
        "language": "python",
        "start": {"line": start_line, "col": start_col},
        "end": {"line": end_line, "col": end_col},
        "match": value,
    }


def test_exact_matches_include_comments_and_strings_and_report_coordinates(tmp_path):
    (tmp_path / "sample.py").write_text(
        '# needle\nvalue = "needle"\nneedle = 1\n', encoding="utf-8"
    )

    result = run_search(tmp_path, [{"id": "exact", "kind": "exact", "pattern": "needle"}])

    assert output_objects(result) == [
        match("exact", "sample.py", 1, 3, 1, 9, "needle"),
        match("exact", "sample.py", 2, 10, 2, 16, "needle"),
        match("exact", "sample.py", 3, 1, 3, 7, "needle"),
    ]


def test_regex_flags_i_m_and_s_are_applied(tmp_path):
    (tmp_path / "flags.py").write_text(
        "HELLO\nhello world\nhello\nworld\n", encoding="utf-8"
    )
    rules = [
        {"id": "case", "kind": "regex", "pattern": "hello", "regex_flags": ["i"]},
        {"id": "line", "kind": "regex", "pattern": "^hello.*$", "regex_flags": ["i", "m"]},
        {"id": "across", "kind": "regex", "pattern": "hello.world", "regex_flags": ["s"]},
    ]

    result = run_search(tmp_path, rules)

    assert output_objects(result) == [
        match("case", "flags.py", 1, 1, 1, 6, "HELLO"),
        match("case", "flags.py", 2, 1, 2, 6, "hello"),
        match("line", "flags.py", 2, 1, 2, 12, "hello world"),
        match("across", "flags.py", 3, 1, 4, 6, "hello\nworld"),
        match("case", "flags.py", 3, 1, 3, 6, "hello"),
        match("line", "flags.py", 3, 1, 3, 6, "hello"),
    ]


def test_default_languages_python_and_empty_language_selection(tmp_path):
    (tmp_path / "language.py").write_text("needle\n", encoding="utf-8")
    rules = [
        {"id": "default", "kind": "exact", "pattern": "needle"},
        {"id": "explicit", "kind": "exact", "pattern": "needle", "languages": ["python"]},
        {"id": "none", "kind": "exact", "pattern": "needle", "languages": []},
    ]

    assert output_objects(run_search(tmp_path, rules)) == [
        match("default", "language.py", 1, 1, 1, 7, "needle"),
        match("explicit", "language.py", 1, 1, 1, 7, "needle"),
    ]


def test_only_lowercase_py_files_are_scanned_and_nested_posix_paths_are_sorted(tmp_path):
    (tmp_path / "z.py").write_text("hit\n", encoding="utf-8")
    nested = tmp_path / "sub" / "a.py"
    nested.parent.mkdir()
    nested.write_text("hit\n", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("hit\n", encoding="utf-8")
    (tmp_path / "ignored.PY").write_text("hit\n", encoding="utf-8")

    result = run_search(tmp_path, [{"id": "h", "kind": "exact", "pattern": "hit"}])

    assert output_objects(result) == [
        match("h", "sub/a.py", 1, 1, 1, 4, "hit"),
        match("h", "z.py", 1, 1, 1, 4, "hit"),
    ]


def test_matches_at_same_position_are_sorted_by_rule_id(tmp_path):
    (tmp_path / "same.py").write_text("x\n", encoding="utf-8")
    rules = [
        {"id": "z-rule", "kind": "exact", "pattern": "x"},
        {"id": "a-rule", "kind": "regex", "pattern": "x"},
    ]

    assert output_objects(run_search(tmp_path, rules)) == [
        match("a-rule", "same.py", 1, 1, 1, 2, "x"),
        match("z-rule", "same.py", 1, 1, 1, 2, "x"),
    ]


def test_empty_rules_and_no_matches_are_successful_and_produce_no_stdout(tmp_path):
    (tmp_path / "empty.py").write_text("nothing here\n", encoding="utf-8")

    no_rules = run_search(tmp_path, [])
    no_match = run_search(tmp_path, [{"id": "x", "kind": "exact", "pattern": "absent"}])

    assert no_rules.stdout == ""
    assert no_match.stdout == ""


def test_files_that_fail_default_utf8_decoding_are_skipped(tmp_path):
    (tmp_path / "valid.py").write_text("needle\n", encoding="utf-8")
    (tmp_path / "broken.py").write_bytes(b"needle\n\xff\n")

    result = run_search(tmp_path, [{"id": "n", "kind": "exact", "pattern": "needle"}])

    assert output_objects(result) == [match("n", "valid.py", 1, 1, 1, 7, "needle")]


def test_requested_encoding_decodes_files_and_preserves_match_text(tmp_path):
    (tmp_path / "latin.py").write_bytes("café\n".encode("latin-1"))

    result = run_search(
        tmp_path,
        [{"id": "accent", "kind": "exact", "pattern": "é"}],
        "--encoding",
        "latin-1",
    )

    assert output_objects(result) == [match("accent", "latin.py", 1, 4, 1, 5, "é")]
