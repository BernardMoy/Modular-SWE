"""Black-box coverage for checkpoint 4's CLI additions.

Every project used here is created in pytest's temporary directory.  The CLI
is invoked as a subprocess so these tests do not depend on implementation
modules, classes, or function signatures.
"""

import json
import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = next(
    (ROOT / name / "sith.py" for name in ("implementation", "previous_implementation")
     if (ROOT / name / "sith.py").is_file()),
    None,
)
if ENTRYPOINT is None:  # pragma: no cover - useful failure when run elsewhere
    pytest.skip("no sith.py implementation directory is present", allow_module_level=True)


def write_project(tmp_path, files):
    for relative, content in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


def cli(project, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ENTRYPOINT.parent) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run(
        ["python", str(ENTRYPOINT), *map(str, args)],
        cwd=project,
        env=env,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_signatures_render_parameters_return_type_docstring_and_self_exclusion(tmp_path):
    project = write_project(tmp_path, {
        "app.py": '''\
class Service:
    def call(self, item: str, count=1, *, verbose: bool = False) -> str:
        """Call the service."""
        return item

result = Service().call("x", count=2, verbose=True)
''',
    })
    data = cli(project, "signatures", project / "app.py", 7, 44)
    signature = next(x for x in data["signatures"] if x["name"] == "call")
    assert signature["params"] == ["item: str", "count=1", "verbose: bool=False"]
    assert signature["description"] == "def call(item: str, count=1, *, verbose: bool=False) -> str"
    assert signature["docstring"] == "Call the service."
    assert signature["index"] == 2


@pytest.mark.parametrize("line, column, expected", [
    ("result = add(1, 2, 3)", 18, 1),
    ("result = add(1, mystery=3)", 20, None),
])
def test_signatures_follow_extra_argument_binding_and_unknown_keywords(tmp_path, line, column, expected):
    project = write_project(tmp_path, {
        "app.py": "def add(first, *rest, **options):\n    return first\n" + line + "\n",
    })
    data = cli(project, "signatures", project / "app.py", 3, column)
    assert data["signatures"][0]["index"] == expected


def test_signatures_outside_call_parentheses_returns_empty_array(tmp_path):
    project = write_project(tmp_path, {"app.py": "def add(x):\n    return x\nname = add\n"})
    assert cli(project, "signatures", project / "app.py", 3, 8) == {"signatures": []}


def test_signatures_return_all_overloads_in_module_line_order(tmp_path):
    project = write_project(tmp_path, {
        "api.py": "from typing import overload\n@overload\ndef read(value: int) -> bytes: ...\n@overload\ndef read(value: str) -> str: ...\nread(1)\n",
    })
    signatures = cli(project, "signatures", project / "api.py", 5, 5)["signatures"]
    assert [item["params"] for item in signatures] == [["value: int"], ["value: str"]]
    assert [item["index"] for item in signatures] == [0, 0]


def test_references_file_scope_includes_definition_and_is_sorted(tmp_path):
    project = write_project(tmp_path, {"mod.py": "value = 1\nprint(value)\nvalue += 1\n"})
    data = cli(project, "references", project / "mod.py", 2, 7)
    assert [(x["line"], x["column"], x["is_definition"]) for x in data["references"]] == [
        (1, 0, True), (2, 6, False), (3, 0, True)
    ]
    assert all(x["module_path"] == "mod.py" for x in data["references"])


def test_references_project_scope_excludes_same_spelling_unrelated_symbol(tmp_path):
    project = write_project(tmp_path, {
        "one.py": "value = 1\nprint(value)\n",
        "two.py": "value = 2\nprint(value)\n",
    })
    data = cli(project, "references", project / "one.py", 2, 6, "--scope", "project")
    assert {(x["module_path"], x["line"]) for x in data["references"]} == {
        ("one.py", 1), ("one.py", 2)
    }


def test_search_is_case_insensitive_ranked_and_omits_local_names_and_usages(tmp_path):
    project = write_project(tmp_path, {
        "a.py": "class Calculator: pass\ndef calc():\n    local_calc = 1\n    return local_calc\n",
        "b.py": "recalculate = 1\nprint(Calculator)\n",
    })
    results = cli(project, "search", "CALC", "--project", project)["results"]
    assert [x["name"] for x in results] == ["calc", "Calculator", "recalculate"]
    assert all("docstring" not in x for x in results)
    assert all(x["name"] != "local_calc" for x in results)


def test_names_default_and_all_scopes_include_imports_and_nested_definitions(tmp_path):
    project = write_project(tmp_path, {
        "mod.py": "import pathlib\nTOP = 1\n\ndef outer(arg):\n    local = arg\n    def inner():\n        return local\n\nclass Box:\n    size = 2\n",
    })
    default = cli(project, "names", project / "mod.py")["names"]
    assert [x["name"] for x in default] == ["pathlib", "TOP", "outer", "Box"]
    assert all(x["is_definition"] is True for x in default)
    all_scopes = cli(project, "names", project / "mod.py", "--all-scopes")["names"]
    assert {x["name"] for x in all_scopes} >= {"pathlib", "TOP", "outer", "arg", "local", "inner", "Box", "size"}
    assert [(x["line"], x["column"]) for x in all_scopes] == sorted(
        (x["line"], x["column"]) for x in all_scopes
    )


def test_adjacent_stub_controls_signatures_and_infer_but_goto_uses_runtime_source(tmp_path):
    project = write_project(tmp_path, {
        "app.py": "from service import fetch\nanswer = fetch('id')\n",
        "service.py": "def fetch(value):\n    return value\n",
        "service.pyi": "def fetch(value: int) -> bytes: ...\n",
    })
    sig = cli(project, "signatures", project / "app.py", 2, 16)["signatures"]
    assert sig[0]["params"] == ["value: int"]
    assert "-> bytes" in sig[0]["description"]
    inferred = cli(project, "infer", project / "app.py", 2, 10)["definitions"]
    assert any(x["type"] == "bytes" for x in inferred)
    target = cli(project, "goto", project / "app.py", 2, 10)["definitions"]
    assert target and target[0]["module_path"] == "service.py"
    assert target[0]["line"] == 1


def test_project_stub_package_supplies_attribute_completion(tmp_path):
    project = write_project(tmp_path, {
        "app.py": "from widgets import Widget\nw = Widget()\nw.\n",
        "widgets.py": "class Widget:\n    pass\n",
        "stubs/widgets/__init__.pyi": "class Widget:\n    title: str\n    count: int\n",
    })
    names = {x["name"] for x in cli(project, "complete", project / "app.py", 3, 2)["completions"]}
    assert {"title", "count"} <= names
