"""Black-box tests for the multi-language code search CLI."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def _entrypoint() -> Path:
    """Find the implementation selected by the test environment."""
    configured = os.environ.get("CODE_SEARCH_ENTRYPOINT")
    if configured:
        return Path(configured).resolve()

    project_root = Path(__file__).resolve().parents[1]
    for relative_path in ("implementation/code_search.py", "previous_implementation/code_search.py"):
        candidate = project_root / relative_path
        if candidate.is_file():
            return candidate
    pytest.fail("could not find code_search.py in implementation/ or previous_implementation/")


def _run_cli(root: Path, rules: list[dict]) -> tuple[subprocess.CompletedProcess[str], list[dict]]:
    entrypoint = _entrypoint()
    rules_file = root / "rules.json"
    rules_file.write_text(json.dumps(rules), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(entrypoint), str(root), "--rules", str(rules_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    records = [json.loads(line) for line in result.stdout.splitlines() if line]
    return result, records


def _write_sources(root: Path, files: dict[str, str]) -> None:
    for relative_path, source in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")


def test_all_required_extensions_are_scanned_and_report_their_language(tmp_path: Path) -> None:
    extensions = {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".hh": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
    }
    files = {
        f"nested/source{extension}": "SUPPORTED_MARKER\n"
        for extension in extensions
    }
    files["ignored.txt"] = "SUPPORTED_MARKER\n"
    files["ignored.py.txt"] = "SUPPORTED_MARKER\n"
    _write_sources(tmp_path, files)

    result, records = _run_cli(
        tmp_path,
        [{"id": "marker", "kind": "exact", "pattern": "SUPPORTED_MARKER"}],
    )

    assert result.returncode == 0, result.stderr
    assert {
        (record["file"], record["language"])
        for record in records
    } == {
        (f"nested/source{extension}", language)
        for extension, language in extensions.items()
    }


def test_rule_languages_limit_matches_to_the_selected_language(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        {
            "main.py": "PY_ONLY JS_ONLY CPP_ONLY\n",
            "app.js": "PY_ONLY JS_ONLY CPP_ONLY\n",
            "engine.cpp": "PY_ONLY JS_ONLY CPP_ONLY\n",
        },
    )
    rules = [
        {"id": "python-rule", "kind": "exact", "pattern": "PY_ONLY", "languages": ["python"]},
        {"id": "javascript-rule", "kind": "exact", "pattern": "JS_ONLY", "languages": ["javascript"]},
        {"id": "cpp-rule", "kind": "exact", "pattern": "CPP_ONLY", "languages": ["cpp"]},
        {"id": "multi-language-rule", "kind": "exact", "pattern": "PY_ONLY", "languages": ["python", "javascript"]},
    ]

    result, records = _run_cli(tmp_path, rules)

    assert result.returncode == 0, result.stderr
    assert {
        (record["rule_id"], record["file"], record["language"])
        for record in records
    } == {
        ("python-rule", "main.py", "python"),
        ("javascript-rule", "app.js", "javascript"),
        ("cpp-rule", "engine.cpp", "cpp"),
        ("multi-language-rule", "main.py", "python"),
        ("multi-language-rule", "app.js", "javascript"),
    }


def test_rule_without_languages_applies_to_python_javascript_and_cpp(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        {
            "a.py": "COMMON\n",
            "b.js": "COMMON\n",
            "c.hpp": "COMMON\n",
        },
    )

    result, records = _run_cli(
        tmp_path,
        [{"id": "all-languages", "kind": "exact", "pattern": "COMMON"}],
    )

    assert result.returncode == 0, result.stderr
    assert {
        (record["file"], record["language"], record["match"])
        for record in records
    } == {
        ("a.py", "python", "COMMON"),
        ("b.js", "javascript", "COMMON"),
        ("c.hpp", "cpp", "COMMON"),
    }


def test_regex_rules_are_applied_with_language_filtering(tmp_path: Path) -> None:
    _write_sources(
        tmp_path,
        {
            "web.mjs": "console.log(42)\n",
            "native.cc": "printf(\"hello\")\n",
            "script.py": "console.log(42) printf(\"hello\")\n",
        },
    )
    rules = [
        {"id": "console", "kind": "regex", "pattern": r"console\.log\s*\(", "languages": ["javascript"]},
        {"id": "printf", "kind": "regex", "pattern": r"\bprintf\s*\(", "languages": ["cpp"]},
    ]

    result, records = _run_cli(tmp_path, rules)

    assert result.returncode == 0, result.stderr
    assert {
        (record["rule_id"], record["file"], record["match"])
        for record in records
    } == {
        ("console", "web.mjs", "console.log("),
        ("printf", "native.cc", "printf("),
    }
