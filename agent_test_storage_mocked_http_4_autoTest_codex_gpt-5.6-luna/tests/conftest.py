import os
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption(
        "--implementation-dir",
        action="store",
        default=os.environ.get("HMOCK_IMPLEMENTATION_DIR"),
        help="Directory containing the hmock.py CLI under test",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "cli: black-box tests for the hmock CLI")


def _entrypoint(config):
    selected = config.getoption("--implementation-dir")
    candidates = ([Path(selected)] if selected else []) + [
        Path("implementation"),
        Path("previous_implementation"),
    ]
    for directory in candidates:
        entrypoint = directory / "hmock.py"
        if entrypoint.is_file():
            return entrypoint.resolve()
    raise RuntimeError("could not find hmock.py; pass --implementation-dir")


def pytest_generate_tests(metafunc):
    if "hmock_entrypoint" in metafunc.fixturenames:
        metafunc.parametrize("hmock_entrypoint", [_entrypoint(metafunc.config)])
