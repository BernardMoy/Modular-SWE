from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _find_import_root(entrypoint: Path) -> Path:
    for candidate in entrypoint.resolve().parents:
        if (candidate / "datasets").is_dir():
            return candidate
    return entrypoint.resolve().parent


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--implementation",
        action="store",
        help="Path to the implementation folder that contains iris.py and requirements.txt.",
    )


@pytest.fixture(scope="session")
def implementation_dir(pytestconfig: pytest.Config) -> Path:
    configured = pytestconfig.getoption("implementation") or os.environ.get(
        "IRIS_IMPLEMENTATION_DIR"
    )
    if not configured:
        pytest.fail(
            "Provide the implementation folder with --implementation or "
            "IRIS_IMPLEMENTATION_DIR."
        )

    path = Path(configured).expanduser().resolve()
    if not path.is_dir():
        pytest.fail(f"Implementation folder is not a directory: {path}")
    if not (path / "iris.py").is_file():
        pytest.fail(f"Implementation folder does not contain iris.py: {path}")
    if not (path / "requirements.txt").is_file():
        pytest.fail(f"Implementation folder does not contain requirements.txt: {path}")
    return path


@pytest.fixture(scope="session")
def isolated_workspace(
    implementation_dir: Path, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    workspace_dir = tmp_path_factory.mktemp("iris_cli_workspace")
    copied_implementation_dir = workspace_dir / "implementation"
    shutil.copytree(implementation_dir, copied_implementation_dir)
    return workspace_dir


@pytest.fixture(scope="session")
def entrypoint(isolated_workspace: Path) -> Path:
    return isolated_workspace / "implementation" / "iris.py"


@pytest.fixture(scope="session")
def cli_python(
    implementation_dir: Path, tmp_path_factory: pytest.TempPathFactory
) -> Path:
    venv_dir = tmp_path_factory.mktemp("iris_cli_venv")
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        cwd=str(implementation_dir),
    )

    bin_dir = "Scripts" if os.name == "nt" else "bin"
    python_exe = venv_dir / bin_dir / ("python.exe" if os.name == "nt" else "python")

    subprocess.run(
        [str(python_exe), "-m", "pip", "install", "-r", str(implementation_dir / "requirements.txt")],
        check=True,
        cwd=str(implementation_dir),
    )
    return python_exe


@pytest.fixture
def run_cli(cli_python: Path, entrypoint: Path, isolated_workspace: Path):
    def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        pythonpath_entries = [str(_find_import_root(entrypoint))]
        if env.get("PYTHONPATH"):
            pythonpath_entries.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

        return subprocess.run(
            [str(cli_python), str(entrypoint), *args],
            cwd=str(cwd or isolated_workspace),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    return _run
