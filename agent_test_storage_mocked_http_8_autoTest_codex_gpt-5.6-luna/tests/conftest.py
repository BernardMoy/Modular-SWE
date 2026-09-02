import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(url, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json"} if body is not None else {},
    )
    try:
        with urlopen(request, timeout=1) as response:
            return response.status, json.loads(response.read() or b"{}")
    except HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


@pytest.fixture
def running_server(tmp_path):
    implementation = Path(
        os.environ.get("HMOCK_IMPLEMENTATION_DIR", str(Path.cwd() / "previous_implementation"))
    ).resolve()

    def start(definitions=None, extra_env=None):
        templates = tmp_path / "templates"
        templates.mkdir(exist_ok=True)
        if definitions is not None:
            (templates / "definitions.yaml").write_text(
                json.dumps(definitions), encoding="utf-8"
            )
        http_port, admin_port = _free_port(), _free_port()
        env = os.environ.copy()
        env.update(
            {
                "HM_TEMPLATES_DIR": str(templates),
                "HM_PERSISTENCE_PATH": str(tmp_path / "persistence.json"),
                "HM_HTTP_HOST": "127.0.0.1",
                "HM_HTTP_PORT": str(http_port),
                "HM_ADMIN_HTTP_HOST": "127.0.0.1",
                "HM_ADMIN_HTTP_PORT": str(admin_port),
                "HM_ADMIN_HTTP_ENABLED": "true",
                "HM_GRPC_HOST": "127.0.0.1",
                "HM_GRPC_PORT": str(_free_port()),
            }
        )
        if extra_env:
            env.update({key: str(value) for key, value in extra_env.items()})
        process = subprocess.Popen(
            [sys.executable, "hmock.py"],
            cwd=implementation,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        base = f"http://127.0.0.1:{admin_port}"
        deadline = time.time() + 5
        while time.time() < deadline:
            if process.poll() is not None:
                break
            try:
                status, _ = _request(base + "/api/v1/health")
                if status == 200:
                    return process, base, http_port
            except Exception:
                pass
            time.sleep(0.05)
        output = process.communicate(timeout=2)
        raise AssertionError(
            "server did not become ready: " + output[1]
        )

    processes = []

    class Server:
        def start(self, definitions=None, extra_env=None):
            process, base, http_port = start(definitions, extra_env)
            processes.append(process)
            return base, http_port

        @staticmethod
        def request(base, payload):
            return _request(base + "/api/v1/evaluate", payload)

    yield Server()
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


@pytest.fixture
def evaluate(running_server):
    base, _ = running_server.start()

    def call(payload):
        return running_server.request(base, payload)

    return call
