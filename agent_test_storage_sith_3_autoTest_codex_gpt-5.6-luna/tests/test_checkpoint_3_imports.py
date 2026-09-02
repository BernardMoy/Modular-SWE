import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_DIR = ROOT / "implementation"
if not IMPLEMENTATION_DIR.is_dir():
    IMPLEMENTATION_DIR = ROOT / "previous_implementation"
ENTRYPOINT = IMPLEMENTATION_DIR / "sith.py"


def write_project(tmp_path, files):
    for relative, contents in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
    return tmp_path


def cli(project, command, file, line, column, *options, timeout=3):
    process = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT),
            command,
            str(project / file),
            str(line),
            str(column),
            *options,
        ],
        cwd=ENTRYPOINT.parent,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout)


def names(result):
    return [item["name"] for item in result["completions"]]


def test_project_root_flag_resolves_modules_outside_the_file_directory(tmp_path):
    write_project(
        tmp_path,
        {
            "src/app.py": "from shared.tools import answer\nvalue = answer\n",
            "shared/__init__.py": "",
            "shared/tools.py": "answer = 42\n",
        },
    )

    result = cli(tmp_path, "goto", "src/app.py", 2, 8, "--project", str(tmp_path))

    assert result["definitions"][0]["name"] == "answer"
    assert result["definitions"][0]["line"] == 1
    assert result["definitions"][0]["module_path"] == "shared/tools.py"


def test_valid_relative_import_resolves_from_the_importing_package(tmp_path):
    write_project(
        tmp_path,
        {
            "pkg/main.py": "from .source import value\nvalue\n",
            "pkg/__init__.py": "",
            "pkg/source.py": "value = 1\n",
        },
    )

    result = cli(
        tmp_path,
        "goto",
        "pkg/main.py",
        2,
        1,
        "--follow-imports",
        "--project",
        str(tmp_path),
    )

    assert result["definitions"][0]["module_path"] == "pkg/source.py"


def test_goto_import_is_import_site_by_default_and_definition_when_followed(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from pkg.source import greet\ngreet()\n",
            "pkg/__init__.py": "",
            "pkg/source.py": "def greet():\n    return 'hi'\n",
        },
    )

    without_following = cli(tmp_path, "goto", "main.py", 2, 1)
    with_following = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports")

    assert without_following["definitions"][0]["line"] == 1
    assert without_following["definitions"][0]["module_path"] == "main.py"
    assert with_following["definitions"][0]["line"] == 1
    assert with_following["definitions"][0]["module_path"] == "pkg/source.py"
    assert with_following["definitions"][0]["type"] == "function"


def test_follow_imports_reaches_the_final_definition_through_an_import_chain(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from middle import value\nvalue\n",
            "middle.py": "from source import value\n",
            "source.py": "value = 7\n",
        },
    )

    result = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports")

    assert result["definitions"][0]["module_path"] == "source.py"
    assert result["definitions"][0]["line"] == 1


def test_infer_resolves_a_definition_and_type_from_another_module(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from models import User\nuser = User()\nuser\n",
            "models.py": "class User:\n    pass\n",
        },
    )

    result = cli(tmp_path, "infer", "main.py", 3, 1)

    assert result["definitions"][0]["name"] == "User"
    assert result["definitions"][0]["type"] == "instance"
    assert result["definitions"][0]["module_path"] == "models.py"


def test_import_and_from_import_completion_use_prefixes_and_visibility_order(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "import al\nfrom lib import \n",
            "alpha.py": "",
            "alpine/__init__.py": "",
            "lib.py": "visible = 1\n_private = 2\n__dunder = 3\n",
        },
    )

    modules = cli(tmp_path, "complete", "main.py", 1, 9)
    imported_names = cli(tmp_path, "complete", "main.py", 2, 16)

    assert names(modules)[:2] == ["alpha", "alpine"]
    assert names(imported_names)[:2] == ["visible", "_private"]
    assert "__dunder" in names(imported_names)


def test_empty_import_completion_suggests_project_modules_and_namespace_packages(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "import \n",
            "alpha.py": "",
            "namespace/mod.py": "value = 1\n",
        },
    )

    result = cli(tmp_path, "complete", "main.py", 1, 7)

    assert "alpha" in names(result)
    assert "namespace" in names(result)


def test_from_import_uses_all_exactly_and_submodule_import_completion(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from pkg import \nfrom pkg.sub import \n",
            "pkg/__init__.py": "__all__ = ['exported']\nexported = 1\nhidden = 2\n",
            "pkg/sub.py": "public = 1\n_private = 2\n",
        },
    )

    package_names = cli(tmp_path, "complete", "main.py", 1, 16)
    submodule_names = cli(tmp_path, "complete", "main.py", 2, 19)

    assert names(package_names) == ["exported"]
    assert names(submodule_names) == ["public"]


def test_star_import_exposes_public_names_and_respects_all(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from source import *\nexported\n",
            "source.py": "__all__ = ['exported']\nexported = 1\nhidden = 2\n",
        },
    )

    result = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports")

    assert result["definitions"][0]["name"] == "exported"
    assert result["definitions"][0]["module_path"] == "source.py"


def test_imported_class_attribute_completion_works_across_files(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from models import User\nuser = User()\nuser.na\n",
            "models.py": "class User:\n    name = 'Ada'\n    _secret = 1\n",
        },
    )

    result = cli(tmp_path, "complete", "main.py", 3, 7)

    assert names(result) == ["name"]


def test_unresolvable_imports_are_non_errors_and_follow_goto_falls_back_to_import(tmp_path):
    write_project(tmp_path, {"main.py": "from does_not_exist import missing\nmissing\n"})

    result = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports")

    assert result["definitions"][0]["module_path"] == "main.py"
    assert result["definitions"][0]["line"] == 1


def test_stdlib_import_is_recognized_for_from_import_completion(tmp_path):
    write_project(tmp_path, {"main.py": "from math import sq\n"})

    result = cli(tmp_path, "complete", "main.py", 1, 16)

    assert "sqrt" in names(result)


def test_relative_import_above_project_root_is_unresolvable(tmp_path):
    write_project(
        tmp_path,
        {
            "pkg/main.py": "from ...outside import value\nvalue\n",
            "pkg/__init__.py": "",
        },
    )

    result = cli(tmp_path, "complete", "pkg/main.py", 1, 22, "--project", str(tmp_path))

    assert "value" not in names(result)


def test_circular_imports_terminate_and_return_available_definitions(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from a import available\navailable\n",
            "a.py": "from b import missing\navailable = 1\n",
            "b.py": "from a import available\n",
        },
    )

    result = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports", timeout=2)

    assert result["definitions"][0]["module_path"] == "a.py"


def test_valid_definitions_before_syntax_error_in_imported_file_remain_resolvable(tmp_path):
    write_project(
        tmp_path,
        {
            "main.py": "from broken import good\ngood\n",
            "broken.py": "good = 1\nthis is not valid python !!!\n",
        },
    )

    result = cli(tmp_path, "goto", "main.py", 2, 1, "--follow-imports")

    assert result["definitions"][0]["module_path"] == "broken.py"
    assert result["definitions"][0]["line"] == 1


@pytest.mark.parametrize("file_name", ["main.py", "pkg/main.py"])
def test_outputs_never_use_backslash_path_separators(tmp_path, file_name):
    relative = Path(file_name)
    write_project(
        tmp_path,
        {
            file_name: "from pkg.mod import value\nvalue\n",
            "pkg/__init__.py": "",
            "pkg/mod.py": "value = 1\n",
        },
    )

    result = cli(tmp_path, "goto", file_name, 2, 1, "--follow-imports")
    serialized = json.dumps(result)

    assert "\\\\" not in serialized
    assert result["definitions"][0]["module_path"] == "pkg/mod.py"
