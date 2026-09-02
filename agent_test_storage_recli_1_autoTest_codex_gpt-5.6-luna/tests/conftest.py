"""Black-box helpers for invoking the appctl executable."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def run_appctl():
    """Run the documented entry point as a separate CLI process."""

    entrypoint = Path(__file__).parents[1] / "implementation" / "appctl.py"

    def run(*args, env=None):
        process_env = None
        if env is not None:
            process_env = dict(env)
        return subprocess.run(
            [sys.executable, str(entrypoint), *map(str, args)],
            text=True,
            capture_output=True,
            env=process_env,
            check=False,
        )

    return run


def help_command_names(help_text):
    """Extract command names from the public, fixed-column help listing.

    The parser intentionally accepts whitespace-separated columns rather than
    importing or inspecting the implementation's command registry.
    """

    names = []
    for line in help_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith(("usage:", "commands:", "options:")):
            continue
        fields = stripped.split(None, 1)
        if len(fields) == 2 and fields[0] not in {"-", "--"}:
            names.append(fields[0])
    return names
