"""Black-box tests for checkpoint 2's type inference and definition navigation.

The CLI is launched as a subprocess so these tests do not depend on any of the
implementation's Python modules or function signatures.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _entrypoint():
    configured = os.environ.get("SITH_ENTRYPOINT")
    if configured:
        return Path(configured)
    for directory in (ROOT / "implementation", ROOT / "previous_implementation"):
        candidate = directory / "sith.py"
        if candidate.is_file():
            return candidate
    pytest.fail("Could not find an implementation/sith.py entrypoint")


def _write_project(tmp_path, source, filename="example.py"):
    path = tmp_path / filename
    path.write_text(source, encoding="utf-8")
    return path


def _run(path, command, line, column):
    result = subprocess.run(
        [sys.executable, str(_entrypoint()), command, str(path), str(line), str(column)],
        cwd=str(_entrypoint().parent),
        text=True,
        capture_output=True,
    )
    payload = None
    if result.stdout.strip():
        payload = json.loads(result.stdout)
    return result, payload


def _at(path, command, line_text, token, occurrence=1):
    lines = path.read_text(encoding="utf-8").splitlines()
    line_number = next(i for i, candidate in enumerate(lines, 1) if candidate == line_text)
    line = line_text
    start = -1
    for _ in range(occurrence):
        start = line.index(token, start + 1)
    return _run(path, command, line_number, start)


def _definition(**values):
    return {
        "name": values["name"],
        "type": values["type"],
        "full_name": values["full_name"],
        "module_path": values.get("module_path", "example.py"),
        "line": values["line"],
        "column": values["column"],
        "description": values["description"],
        "docstring": values.get("docstring", ""),
    }


def test_goto_reports_exact_function_definition_metadata(tmp_path):
    source = '''
def add(left, right):
    """Add two values."""
    return left + right

result = add(1, 2)
'''
    path = _write_project(tmp_path, source)
    result, payload = _at(path, "goto", "result = add(1, 2)", "add")

    assert result.returncode == 0
    assert payload == {
        "definitions": [
            _definition(
                name="add", type="function", full_name="example.add", line=2,
                column=4, description="def add(left, right)",
                docstring="Add two values.",
            )
        ]
    }


def test_goto_distinguishes_assignment_and_import_bindings(tmp_path):
    source = '''import math as maths
value = 1
alias = value
'''
    path = _write_project(tmp_path, source)

    imported, imported_payload = _at(path, "goto", "import math as maths", "maths")
    assigned, assigned_payload = _at(path, "goto", "alias = value", "value")

    assert imported.returncode == assigned.returncode == 0
    assert imported_payload["definitions"][0] == _definition(
        name="maths", type="module", full_name="example.maths", line=1,
        column=0, description="import maths",
    )
    assert assigned_payload["definitions"][0] == _definition(
        name="value", type="instance", full_name="example.value", line=2,
        column=0, description="instance of int",
    )


def test_infer_literals_and_assignment_chain(tmp_path):
    source = '''number = 42
text = "hello"
copied = number
none_value = None
'''
    path = _write_project(tmp_path, source)

    number, number_payload = _at(path, "infer", "number = 42", "42")
    copied, copied_payload = _at(path, "infer", "copied = number", "number")
    none_value, none_payload = _at(path, "infer", "none_value = None", "None")

    for result in (number, copied, none_value):
        assert result.returncode == 0
    assert number_payload["definitions"][0]["full_name"] == "builtins.int"
    assert number_payload["definitions"][0]["type"] == "instance"
    assert copied_payload["definitions"][0]["full_name"] == "builtins.int"
    assert none_payload["definitions"][0]["full_name"] == "builtins.None"
    assert none_payload["definitions"][0]["module_path"] == ""
    assert none_payload["definitions"][0]["line"] == none_payload["definitions"][0]["column"] == 0


def test_infer_function_returns_all_possible_types_and_none_for_no_return(tmp_path):
    source = '''\ndef choose(flag):
    if flag:
        return 1
    return "one"

def empty():
    pass

a = choose(True)
b = empty()
'''
    path = _write_project(tmp_path, source)
    choose_result, choose_payload = _at(path, "infer", "a = choose(True)", "choose")
    empty_result, empty_payload = _at(path, "infer", "b = empty()", "empty")

    assert choose_result.returncode == empty_result.returncode == 0
    assert {d["full_name"] for d in choose_payload["definitions"]} == {
        "builtins.int", "builtins.str"
    }
    assert empty_payload["definitions"][0]["full_name"] == "builtins.None"


def test_infer_class_instantiation_and_instance_attribute(tmp_path):
    source = '''class Calculator:
    """A calculator."""
    def __init__(self):
        self.total = 0

    def reset(self):
        return self.total

calc = Calculator()
answer = calc.total
'''
    path = _write_project(tmp_path, source)
    instance_result, instance_payload = _at(path, "infer", "calc = Calculator()", "Calculator")
    attr_result, attr_payload = _at(path, "infer", "answer = calc.total", "total")

    assert instance_result.returncode == attr_result.returncode == 0
    instance = instance_payload["definitions"][0]
    assert instance["name"] == "Calculator" and instance["type"] == "instance"
    assert instance["full_name"] == "example.Calculator"
    assert instance["line"] == 1 and instance["column"] == 6
    assert instance["description"] == "class Calculator"
    assert instance["docstring"] == "A calculator."
    assert attr_payload["definitions"][0]["full_name"] == "builtins.int"


@pytest.mark.parametrize("decorator", ["@dataclasses.dataclass", "@dc.dataclass", "@dataclass", "@d.dataclass(frozen=True)"])
def test_dataclass_fields_are_available_for_attribute_completion_and_inference(tmp_path, decorator):
    if decorator == "@dataclass":
        imports = "from dataclasses import dataclass"
    elif decorator == "@dc.dataclass":
        imports = "import dataclasses as dc"
    elif decorator == "@d.dataclass(frozen=True)":
        imports = "import dataclasses as d"
    else:
        imports = "import dataclasses"
    source = f'''{imports}
{decorator}
class User:
    name: str
    age: int

user = User("Ada", 36)
name_value = user.name
user.
'''
    path = _write_project(tmp_path, source)
    completion, completion_payload = _run(path, "complete", 9, len("user."))
    inferred, inferred_payload = _at(path, "infer", "name_value = user.name", "name", occurrence=2)

    assert completion.returncode == 0
    assert {item["name"] for item in completion_payload["completions"]} >= {"name", "age"}
    assert inferred.returncode == 0
    assert inferred_payload["definitions"][0]["full_name"] == "builtins.str"


def test_infer_narrows_isinstance_branch_and_completion_uses_narrowed_attributes(tmp_path):
    source = '''class Dog:
    def bark(self):
        pass

class Cat:
    def meow(self):
        pass

animal = Dog()
if isinstance(animal, Cat):
    narrowed = animal
    animal.
'''
    path = _write_project(tmp_path, source)
    inferred, payload = _at(path, "infer", "    narrowed = animal", "animal")
    completed, completion_payload = _run(path, "complete", 12, len("    animal."))

    assert inferred.returncode == 0
    assert payload["definitions"][0]["full_name"] == "example.Cat"
    assert completed.returncode == 0
    assert "meow" in {item["name"] for item in completion_payload["completions"]}


def test_union_attribute_completion_contains_attributes_from_all_possible_types(tmp_path):
    source = '''class Left:
    def left_only(self):
        pass

class Right:
    def right_only(self):
        pass

value = Left() if flag else Right()
value.
'''
    path = _write_project(tmp_path, source)
    result, payload = _run(path, "complete", 10, len("value."))

    assert result.returncode == 0
    names = {item["name"] for item in payload["completions"]}
    assert {"left_only", "right_only"} <= names


@pytest.mark.parametrize("command", ["infer", "goto"])
def test_non_name_cursor_is_an_error(command, tmp_path):
    path = _write_project(tmp_path, "value = 123\n")
    result, payload = _run(path, command, 1, len("value = "))

    assert result.returncode == 1
    assert payload is None


@pytest.mark.parametrize("command", ["infer", "goto"])
def test_unresolved_name_returns_empty_definitions(command, tmp_path):
    path = _write_project(tmp_path, "result = missing_name\n")
    result, payload = _at(path, command, "result = missing_name", "missing_name")

    assert result.returncode == 0
    assert payload == {"definitions": []}


def test_definitions_from_multiple_reachable_assignments_are_sorted(tmp_path):
    source = '''if flag:
    value = 1
else:
    value = "text"

result = value
'''
    path = _write_project(tmp_path, source)
    result, payload = _at(path, "goto", "result = value", "value")

    assert result.returncode == 0
    definitions = payload["definitions"]
    assert [d["line"] for d in definitions] == [2, 4]
    assert [(d["module_path"], d["line"], d["column"]) for d in definitions] == [
        ("example.py", 2, 4), ("example.py", 4, 4)
    ]
