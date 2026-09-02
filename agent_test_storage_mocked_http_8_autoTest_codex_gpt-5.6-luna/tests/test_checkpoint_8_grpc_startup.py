import os
import json
import socket
import subprocess
import sys
import time
from pathlib import Path


def _port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run_server(tmp_path, definitions, descriptor):
    implementation = Path(os.environ.get("HMOCK_IMPLEMENTATION_DIR", str(Path.cwd() / "previous_implementation"))).resolve()
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "definitions.yaml").write_text(json.dumps(definitions), encoding="utf-8")
    env = os.environ.copy()
    env.update({
        "HM_TEMPLATES_DIR": str(templates),
        "HM_PERSISTENCE_PATH": str(tmp_path / "state.json"),
        "HM_HTTP_HOST": "127.0.0.1",
        "HM_HTTP_PORT": str(_port()),
        "HM_ADMIN_HTTP_HOST": "127.0.0.1",
        "HM_ADMIN_HTTP_PORT": str(_port()),
        "HM_GRPC_ENABLED": "true",
        "HM_GRPC_HOST": "127.0.0.1",
        "HM_GRPC_PORT": str(_port()),
        "HM_GRPC_DESCRIPTOR_SET_PATHS": descriptor,
    })
    process = subprocess.Popen([sys.executable, "hmock.py"], cwd=implementation, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + 3
    while time.time() < deadline and process.poll() is None:
        time.sleep(0.05)
    was_running = process.poll() is None
    if was_running:
        process.terminate()
        process.wait(timeout=2)
    output = process.stderr.read()
    return process.returncode, output, was_running


def test_grpc_enabled_without_grpc_behaviors_does_not_require_descriptors(tmp_path):
    returncode, stderr, was_running = _run_server(
        tmp_path, [], str(tmp_path / "missing-descriptor.pb")
    )
    assert was_running
    # A running server is terminated by this test; a startup failure is not acceptable.
    assert "startup failed" not in stderr.lower()


def test_grpc_behavior_requires_a_readable_valid_descriptor_set(tmp_path):
    definitions = [{
        "key": "grpc-behavior",
        "expect": {"grpc": {"service": "pkg.Service", "method": "Get"}},
        "actions": [],
    }]
    returncode, _, was_running = _run_server(
        tmp_path, definitions, str(tmp_path / "missing-descriptor.pb")
    )
    assert not was_running
    assert returncode == 1
