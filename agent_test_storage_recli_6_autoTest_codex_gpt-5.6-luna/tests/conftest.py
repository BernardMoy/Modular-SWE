import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def appctl_entrypoint():
    """Locate the implementation under test without importing its internals."""
    configured = os.environ.get("APPCTL_ENTRYPOINT")
    if configured:
        return Path(configured)
    return Path(__file__).parents[1] / "previous_implementation" / "appctl.py"


@pytest.fixture
def project(tmp_path):
    (tmp_path / "appctl.yml").write_text(
        """services:
  database:
    image: postgres:16
  web:
    image: example/web
    depends_on: [database]
volumes:
  uploads: {}
networks:
  frontend: {}
"""
    )
    return tmp_path


@pytest.fixture
def fake_runtime(tmp_path, monkeypatch):
    calls = tmp_path / "runtime-calls.jsonl"
    runtime = tmp_path / "container-runtime"
    runtime.write_text(
        """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

args = sys.argv[1:]
Path(os.environ['RUNTIME_CALL_LOG']).open('a').write(json.dumps(args) + '\\n')
state = os.environ.get('RUNTIME_CONTAINER_STATE', 'missing')
if args[:1] == ['inspect']:
    if state == 'running':
        print(json.dumps([{'State': {'Status': 'running'}}]))
        raise SystemExit(0)
    if state == 'exited':
        print(json.dumps([{'State': {'Status': 'exited'}}]))
        raise SystemExit(0)
    raise SystemExit(1)
if args[:1] == ['ps']:
    raise SystemExit(0)
raise SystemExit(int(os.environ.get('RUNTIME_EXIT_CODE', '0')))
"""
    )
    runtime.chmod(runtime.stat().st_mode | stat.S_IXUSR)
    # Implementations may select either supported runtime name; both resolve
    # to the same observable test double.
    for name in ("docker", "podman", "docker-compose"):
        alias = tmp_path / name
        alias.symlink_to(runtime)
    monkeypatch.setenv("RUNTIME_CALL_LOG", str(calls))
    monkeypatch.setenv("PATH", str(tmp_path) + os.pathsep + os.environ.get("PATH", ""))
    return calls


def read_calls(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.fixture
def run_appctl(appctl_entrypoint, tmp_path):
    def run(*args, cwd=tmp_path, env=None, input_text=None):
        process_env = os.environ.copy()
        process_env.update({"APPCTL_ROOT_DIR": str(tmp_path / "root")})
        if env:
            process_env.update({str(k): str(v) for k, v in env.items()})
        return subprocess.run(
            [sys.executable, str(appctl_entrypoint), *map(str, args)],
            cwd=cwd,
            env=process_env,
            input=input_text,
            text=True,
            capture_output=True,
        )

    return run
