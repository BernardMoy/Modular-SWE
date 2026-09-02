"""Black-box tests for the sith completion command.

The implementation is deliberately invoked as a subprocess.  These tests only
depend on the command line contract and on temporary source files created by
the tests.
"""

from __future__ import annotations

import json
import keyword
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "implementation" / "sith.py"


def run_cli(tmp_path: Path, source: str, line: int, col: int, *extra: str):
    source_file = tmp_path / "subject.py"
    source_file.write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(ENTRYPOINT), "complete", str(source_file), str(line), str(col), *extra],
        text=True,
        capture_output=True,
    )


def completions(result):
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout.endswith("\n")
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert set(payload) == {"completions"}
    assert isinstance(payload["completions"], list)
    for item in payload["completions"]:
        assert set(item) == {"name", "complete", "type", "description"}
        assert isinstance(item["name"], str)
        assert isinstance(item["complete"], str)
        assert item["type"] in {"module", "class", "function", "instance", "statement", "param", "keyword"}
        assert isinstance(item["description"], str)
    return payload["completions"]


def names(items):
    return [item["name"] for item in items]


def by_name(items, name):
    return next(item for item in items if item["name"] == name)


def test_name_completion_scopes_visibility_and_keyword_contract(tmp_path):
    source = """\
module_value = 1
future_global = 2
def outer(outer_param):
    outer_value = 3
    def inner(inner_param):
        inner_value = 4
        later_inner = 5
        
"""
    items = completions(run_cli(tmp_path, source, 8, 4))
    found = set(names(items))
    assert {"module_value", "outer_param", "outer_value", "inner_param", "inner_value"} <= found
    assert "future_global" not in found
    assert "later_inner" in found  # definitions are visible from their statement line
    assert {"def", "class", "return", "if"} <= found
    assert all(items[i]["name"] != items[j]["name"] for i in range(len(items)) for j in range(i))

    assert by_name(items, "outer_param")["type"] == "param"
    assert by_name(items, "module_value")["description"] == "instance of int"
    assert by_name(items, "def")["type"] == "keyword"
    assert by_name(items, "def")["description"] == "def"


def test_prefix_case_insensitive_and_completion_text(tmp_path):
    source = """\
Amazing = 1
another = 2
class Alpha: pass
Ama
"""
    items = completions(run_cli(tmp_path, source, 4, 3))
    assert names(items) == ["Amazing"]
    assert by_name(items, "Amazing")["complete"] == "zing"


def test_fuzzy_prefix_is_opt_in_and_case_insensitive(tmp_path):
    source = """\
camelCaseValue = 1
completely_different = 2
cmv
"""
    exact = completions(run_cli(tmp_path, source, 3, 3))
    fuzzy = completions(run_cli(tmp_path, source, 3, 3, "--fuzzy"))
    assert "camelCaseValue" not in names(exact)
    assert "camelCaseValue" in names(fuzzy)
    assert by_name(fuzzy, "camelCaseValue")["complete"] == "elCaseValue"


def test_ordering_public_private_dunder_then_keywords(tmp_path):
    source = """\
zebra = 1
Apple = 2
_z_private = 3
_a_private = 4
__z__ = 5
__a__ = 6

"""
    result = completions(run_cli(tmp_path, source, 7, 0))
    actual = names(result)
    expected_names = {"zebra", "Apple", "_z_private", "_a_private", "__z__", "__a__"}
    selected = [name for name in actual if name in expected_names]
    assert selected == ["Apple", "zebra", "_a_private", "_z_private", "__a__", "__z__"]
    assert all(name not in expected_names for name in actual[actual.index("__z__") + 1 :])
    assert all(not name.startswith("_") for name in actual[: actual.index("_a_private")])
    assert all(not name.startswith("_") for name in actual if name in keyword.kwlist)


def test_attribute_completion_classes_inheritance_instances_and_init(tmp_path):
    source = """\
class Parent:
    inherited_class_value = 1
    def inherited_method(self): pass
class Child(Parent):
    child_class_value = 2
    def __init__(self):
        self.created_value = 3
    def child_method(self): pass
obj = Child()
obj.
"""
    items = completions(run_cli(tmp_path, source, 10, 4))
    found = set(names(items))
    assert {"inherited_class_value", "inherited_method", "child_class_value", "child_method", "created_value"} <= found
    assert "return" not in found
    assert by_name(items, "child_method")["type"] == "function"


def test_attribute_completion_literals_filters_prefix_and_excludes_keywords(tmp_path):
    source = """\
text = "hello"
text.
values = []
values.ap
mapping = {}
things = set()
"""
    string_items = completions(run_cli(tmp_path, source, 2, 5))
    assert "upper" in names(string_items)
    assert "append" not in names(string_items)
    assert "return" not in names(string_items)

    list_items = completions(run_cli(tmp_path, source, 4, 7))
    assert "append" in names(list_items)
    assert "upper" not in names(list_items)

    prefix_items = completions(run_cli(tmp_path, source, 4, 9))
    assert names(prefix_items) == ["append"]
    assert by_name(prefix_items, "append")["complete"] == "ppend"


def test_imported_module_and_local_star_import(tmp_path):
    (tmp_path / "helper.py").write_text("public_helper = 1\n_hidden_helper = 2\n", encoding="utf-8")
    source = """\
import os
from helper import *
os.
"""
    items = completions(run_cli(tmp_path, source, 3, 0))
    assert by_name(items, "os")["type"] == "module"
    assert "public_helper" in names(items)
    assert "_hidden_helper" not in names(items)

    os_attrs = completions(run_cli(tmp_path, source, 4, 3))
    assert "path" in names(os_attrs)
    assert all(not name.startswith("_") for name in names(os_attrs))


def test_error_cases_are_stderr_and_exit_one(tmp_path):
    missing = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "complete", str(tmp_path / "missing.py"), "1", "0"],
        text=True,
        capture_output=True,
    )
    assert missing.returncode == 1
    assert missing.stderr
    assert missing.stdout == ""

    directory = tmp_path / "directory"
    directory.mkdir()
    directory_result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "complete", str(directory), "1", "0"],
        text=True,
        capture_output=True,
    )
    assert directory_result.returncode == 1
    assert directory_result.stderr

    valid = tmp_path / "valid.py"
    valid.write_text("x = 1\n", encoding="utf-8")
    for line, col in ((3, 0), (1, 6)):
        result = subprocess.run(
            [sys.executable, str(ENTRYPOINT), "complete", str(valid), str(line), str(col)],
            text=True,
            capture_output=True,
        )
        assert result.returncode == 1
        assert result.stderr
        assert result.stdout == ""

    invalid_utf8 = tmp_path / "invalid.py"
    invalid_utf8.write_bytes(b"x = '\xff'\n")
    result = subprocess.run(
        [sys.executable, str(ENTRYPOINT), "complete", str(invalid_utf8), "1", "0"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert result.stderr


def test_syntax_errors_are_tolerated_and_partial_definitions_used(tmp_path):
    source = """\
known = 1
visible = 2
(

"""
    items = completions(run_cli(tmp_path, source, 4, 0))
    assert "known" in names(items)
    assert "visible" in names(items)


def test_zero_completions_is_still_successful_json(tmp_path):
    source = """\
value = object()
value.zzzz
"""
    items = completions(run_cli(tmp_path, source, 2, 10))
    assert isinstance(items, list)
    assert items == []
