"""Black-box tests for checkpoint 5's additional CLI languages.

The implementation under test is selected with CODE_SEARCH_IMPLEMENTATION.
When the variable is unset, use the repository's previous implementation;
this makes the pre-implementation failure check explicit and reproducible.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _entrypoint() -> Path:
    configured = os.environ.get("CODE_SEARCH_IMPLEMENTATION")
    implementation = Path(configured) if configured else ROOT / "previous_implementation"
    if not implementation.is_absolute():
        implementation = ROOT / implementation
    return implementation / "code_search.py"


def _run(root: Path, rules, *flags):
    rules_file = root / "rules.json"
    rules_file.write_text(json.dumps(rules), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(_entrypoint()), str(root), "--rules", str(rules_file), *flags],
        text=True,
        capture_output=True,
        check=False,
    )


def _records(result):
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines() if line]


NEW_LANGUAGES = {
    "rust": ("main.rs", 'println!("hi");'),
    "java": ("Main.java", 'System.out.println("hi");'),
    "go": ("main.go", 'log.Println("hi")'),
    "haskell": ("Main.hs", 'putStrLn "hi"'),
}


def test_each_new_extension_is_discovered_and_reports_its_language(tmp_path):
    for filename, source in NEW_LANGUAGES.values():
        (tmp_path / filename).write_text(source, encoding="utf-8")
    # .lhs is a supported Haskell extension too; an unlisted extension is not.
    (tmp_path / "Literate.lhs").write_text('putStrLn "lhs"', encoding="utf-8")
    (tmp_path / "ignored.rs.txt").write_text('println!("no")', encoding="utf-8")
    (tmp_path / "UPPER.RS").write_text('println!("no")', encoding="utf-8")

    rules = [{"id": "all", "kind": "regex", "pattern": r"(?:println|putStrLn|System\.out\.println|log\.Println)"}]
    records = _records(_run(tmp_path, rules))

    assert {record["language"] for record in records} == set(NEW_LANGUAGES) | {"haskell"}
    assert {record["file"] for record in records} == {
        "Main.hs", "Literate.lhs", "Main.java", "main.go", "main.rs"
    }
    assert [record["file"] for record in records] == sorted(record["file"] for record in records)


@pytest.mark.parametrize("language,filename,source,pattern,capture", [
    ("rust", "main.rs", 'println!("hi");', 'println!($MSG)', '"hi"'),
    ("java", "Main.java", 'System.out.println("hi");', 'System.out.println($X)', '"hi"'),
    ("go", "main.go", 'log.Println("hi")', 'log.Println($ARGS)', '"hi"'),
    ("haskell", "Main.hs", 'putStrLn "hi"', 'putStrLn $MSG', '"hi"'),
])
def test_pattern_rules_match_and_capture_each_new_language(
    tmp_path, language, filename, source, pattern, capture
):
    (tmp_path / filename).write_text(source, encoding="utf-8")
    records = _records(_run(tmp_path, [{
        "id": "new-pattern",
        "kind": "pattern",
        "languages": [language],
        "pattern": pattern,
    }]))

    assert len(records) == 1
    assert records[0]["language"] == language
    assert records[0]["match"] == source.rstrip(";")
    assert records[0]["captures"][next(iter(records[0]["captures"]))]["text"] == capture


def test_omitted_languages_means_all_new_languages_but_empty_is_none(tmp_path):
    for filename, source in NEW_LANGUAGES.values():
        (tmp_path / filename).write_text(source, encoding="utf-8")
    rules = [{"id": "default", "kind": "exact", "pattern": '"hi"'}]
    assert {r["language"] for r in _records(_run(tmp_path, rules))} == set(NEW_LANGUAGES)

    no_languages = [{"id": "none", "kind": "exact", "languages": [], "pattern": '"hi"'}]
    assert _records(_run(tmp_path, no_languages)) == []


def test_language_filter_does_not_leak_across_new_languages(tmp_path):
    for filename, source in NEW_LANGUAGES.values():
        (tmp_path / filename).write_text(source, encoding="utf-8")
    records = _records(_run(tmp_path, [{
        "id": "only-go", "kind": "regex", "languages": ["go"], "pattern": r"hi"
    }]))
    assert [(r["file"], r["language"]) for r in records] == [("main.go", "go")]


@pytest.mark.parametrize("language", sorted(NEW_LANGUAGES))
def test_selector_node_validation_accepts_each_new_language(tmp_path, language):
    filename, _ = NEW_LANGUAGES[language]
    (tmp_path / filename).write_text("x", encoding="utf-8")
    records = _records(_run(tmp_path, [{
        "id": "program", "kind": "selector", "languages": [language], "selector": "program"
    }]))
    assert len(records) == 1
    assert records[0]["language"] == language


@pytest.mark.parametrize("language", ["rust", "java", "go", "haskell"])
def test_unknown_or_case_variant_language_is_rejected(language, tmp_path):
    bad = language.upper() if language != "haskell" else "Haskell"
    result = _run(tmp_path, [{"id": "bad", "kind": "exact", "languages": [bad], "pattern": "x"}])
    assert result.returncode == 2
    assert result.stdout == ""


def test_apply_fixes_writes_new_language_and_dry_run_does_not(tmp_path):
    path = tmp_path / "main.go"
    path.write_text('log.Println("hi")', encoding="utf-8")
    rules = [{
        "id": "replace-go", "kind": "pattern", "languages": ["go"],
        "pattern": "log.Println($ARGS)",
        "fix": {"kind": "replace", "template": "logger.Println($ARGS)"},
    }]

    dry_records = _records(_run(tmp_path, rules, "--dry-run"))
    assert path.read_text(encoding="utf-8") == 'log.Println("hi")'
    fix = next(record for record in dry_records if record.get("event") == "fix")
    assert fix["language"] == "go"
    assert fix["applied"] is False
    assert fix["skipped_reason"] is None
    assert fix["replacement"] == 'logger.Println("hi")'

    apply_records = _records(_run(tmp_path, rules, "--apply-fixes"))
    assert path.read_text(encoding="utf-8") == 'logger.Println("hi")'
    assert next(record for record in apply_records if record.get("event") == "fix")["applied"] is True


def test_selector_field_validation_rejects_an_unknown_selector_for_new_language(tmp_path):
    (tmp_path / "main.rs").write_text("x", encoding="utf-8")
    result = _run(tmp_path, [{
        "id": "bad-selector", "kind": "selector", "languages": ["rust"],
        "selector": "not_a_selector",
    }])
    assert result.returncode == 2
    assert result.stdout == ""
