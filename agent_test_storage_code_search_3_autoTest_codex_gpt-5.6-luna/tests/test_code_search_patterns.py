import json
import subprocess
import sys
from pathlib import Path


ENTRYPOINT = Path(__file__).parents[1] / "implementation" / "code_search.py"


def run_search(root, rules, *, encoding="utf-8"):
    rules_path = Path(root) / "rules.json"
    rules_path.write_text(json.dumps(rules), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), str(root), "--rules", str(rules_path), "--encoding", encoding],
        text=True,
        capture_output=True,
    )


def jsonl(result):
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in result.stdout.splitlines()]


def test_pattern_matches_code_and_ignores_comment_text(tmp_path):
    (tmp_path / "main.py").write_text(
        'print("hello")\n# print(name)\nprint(greeting())\n', encoding="utf-8"
    )

    result = run_search(
        tmp_path,
        [{"id": "call", "kind": "pattern", "pattern": "print($ARG)", "languages": ["python"]}],
    )

    assert jsonl(result) == [
        {
            "rule_id": "call",
            "file": "main.py",
            "language": "python",
            "start": {"line": 1, "col": 1},
            "end": {"line": 1, "col": 14},
            "match": 'print("hello")',
            "captures": {
                "$ARG": {
                    "text": '"hello"',
                    "ranges": [{"start": {"line": 1, "col": 7}, "end": {"line": 1, "col": 14}}],
                }
            },
        },
        {
            "rule_id": "call",
            "file": "main.py",
            "language": "python",
            "start": {"line": 3, "col": 1},
            "end": {"line": 3, "col": 17},
            "match": "print(greeting())",
            "captures": {
                "$ARG": {
                    "text": "greeting()",
                    "ranges": [{"start": {"line": 3, "col": 7}, "end": {"line": 3, "col": 17}}],
                }
            },
        },
    ]


def test_pattern_repeated_metavariable_requires_same_text_and_reports_all_ranges(tmp_path):
    (tmp_path / "app.js").write_text(
        'console.log("user", "user");\nconsole.log("user", id);\n', encoding="utf-8"
    )
    result = run_search(
        tmp_path,
        [{"id": "same", "kind": "pattern", "pattern": "console.log($TAG, $TAG)", "languages": ["javascript"]}],
    )

    matches = jsonl(result)
    assert len(matches) == 1
    assert matches[0]["match"] == 'console.log("user", "user")'
    assert matches[0]["captures"] == {
        "$TAG": {
            "text": '"user"',
            "ranges": [
                {"start": {"line": 1, "col": 13}, "end": {"line": 1, "col": 19}},
                {"start": {"line": 1, "col": 21}, "end": {"line": 1, "col": 27}},
            ],
        }
    }


def test_pattern_supports_nested_expressions(tmp_path):
    (tmp_path / "nested.py").write_text("f(g(h(z)))\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [{"id": "nested", "kind": "pattern", "pattern": "$X($Y)", "languages": ["python"]}],
    )

    assert jsonl(result) == [
        {
            "rule_id": "nested",
            "file": "nested.py",
            "language": "python",
            "start": {"line": 1, "col": 1},
            "end": {"line": 1, "col": 11},
            "match": "f(g(h(z)))",
            "captures": {
                "$X": {"text": "f", "ranges": [{"start": {"line": 1, "col": 1}, "end": {"line": 1, "col": 2}}]},
                "$Y": {"text": "g(h(z))", "ranges": [{"start": {"line": 1, "col": 3}, "end": {"line": 1, "col": 10}}]},
            },
        }
    ]


def test_optional_metavariable_matches_with_and_without_element(tmp_path):
    (tmp_path / "calls.py").write_text("print()\nprint(value)\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [{"id": "optional", "kind": "pattern", "pattern": "print($VALUE?)", "languages": ["python"]}],
    )

    matches = jsonl(result)
    assert [match["match"] for match in matches] == ["print()", "print(value)"]
    assert matches[0]["captures"] == {}
    assert matches[1]["captures"]["$VALUE"]["text"] == "value"


def test_double_dollar_matches_literal_dollar(tmp_path):
    (tmp_path / "prices.js").write_text("const $5 = 1;\nconst $amount = 2;\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [{"id": "dollar", "kind": "pattern", "pattern": "$$5", "languages": ["javascript"]}],
    )

    matches = jsonl(result)
    assert len(matches) == 1
    assert matches[0]["match"] == "$5"
    assert matches[0]["captures"] == {}


def test_pattern_applies_to_default_all_languages_and_respects_language_filter(tmp_path):
    (tmp_path / "a.py").write_text("answer = 1\n", encoding="utf-8")
    (tmp_path / "b.js").write_text("const answer = 1;\n", encoding="utf-8")
    (tmp_path / "c.cpp").write_text("int answer = 1;\n", encoding="utf-8")
    result = run_search(tmp_path, [{"id": "assignment", "kind": "pattern", "pattern": "$NAME = $VALUE"}])

    matches = jsonl(result)
    assert [(m["file"], m["language"]) for m in matches] == [
        ("a.py", "python"),
        ("b.js", "javascript"),
        ("c.cpp", "cpp"),
    ]
    assert [m["captures"]["$NAME"]["text"] for m in matches] == ["answer"] * 3


def test_pattern_positions_use_one_based_unicode_columns(tmp_path):
    (tmp_path / "unicode.py").write_text('π = 1; print(éx)\n', encoding="utf-8")
    result = run_search(
        tmp_path,
        [{"id": "call", "kind": "pattern", "pattern": "print($X)", "languages": ["python"]}],
    )

    match = jsonl(result)[0]
    assert match["start"] == {"line": 1, "col": 8}
    assert match["end"] == {"line": 1, "col": 17}
    assert match["captures"]["$X"] == {
        "text": "éx",
        "ranges": [{"start": {"line": 1, "col": 14}, "end": {"line": 1, "col": 16}}],
    }


def test_same_start_is_sorted_by_end_then_rule_id_and_capture_keys_are_lexical(tmp_path):
    (tmp_path / "order.py").write_text("f(x, y)\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [
            {"id": "z-long", "kind": "pattern", "pattern": "f($Z, $A)"},
            {"id": "b-short", "kind": "exact", "pattern": "f"},
        ],
    )

    matches = jsonl(result)
    assert [(m["rule_id"], m["start"], m["end"]) for m in matches] == [
        ("b-short", {"line": 1, "col": 1}, {"line": 1, "col": 2}),
        ("z-long", {"line": 1, "col": 1}, {"line": 1, "col": 8}),
    ]
    assert list(matches[1]["captures"]) == ["$A", "$Z"]


def test_exact_and_regex_rules_remain_supported_alongside_patterns(tmp_path):
    (tmp_path / "mixed.py").write_text("TODO: print(ok)\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [
            {"id": "todo", "kind": "exact", "pattern": "TODO:"},
            {"id": "call", "kind": "pattern", "pattern": "print($X)", "languages": ["python"]},
            {"id": "word", "kind": "regex", "pattern": r"print", "regex_flags": []},
        ],
    )

    matches = jsonl(result)
    assert [m["rule_id"] for m in matches] == ["todo", "call", "word"]
    assert "captures" not in matches[0]
    assert "captures" not in matches[2]


def test_invalid_pattern_rule_is_reported_as_cli_error(tmp_path):
    (tmp_path / "bad.py").write_text("print(1)\n", encoding="utf-8")
    result = run_search(
        tmp_path,
        [{"id": "broken", "kind": "pattern", "pattern": "print($X"}],
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "broken" in result.stderr


def test_pattern_rule_rejects_unknown_language(tmp_path):
    result = run_search(
        tmp_path,
        [{"id": "bad-language", "kind": "pattern", "pattern": "$X", "languages": ["ruby"]}],
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "languages" in result.stderr
