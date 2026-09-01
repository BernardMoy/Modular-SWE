"""Black-box acceptance tests for checkpoint 3.

The server is exercised only through its command-line entrypoint and HTTP
interface.  The temporary template directory is deliberately created by each
test so these tests do not rely on repository fixtures.
"""

import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
_requested_impl = os.environ.get("HMOCK_IMPLEMENTATION")
if _requested_impl:
    ENTRYPOINT = Path(_requested_impl) / "hmock.py"
else:
    _default_impl = PROJECT_ROOT / "implementation"
    ENTRYPOINT = (
        _default_impl / "hmock.py"
        if _default_impl.is_dir()
        else PROJECT_ROOT / "previous_implementation" / "hmock.py"
    )


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(port, process):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return
        except OSError:
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise AssertionError(
                    f"hmock exited during startup ({process.returncode}): {stderr}"
                )
            time.sleep(0.02)
    raise AssertionError("hmock did not start")


@pytest.fixture
def hmock(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()

    def launch(document):
        (templates / "behaviors.yaml").write_text(document, encoding="utf-8")
        port = free_port()
        env = os.environ.copy()
        env.update(
            HM_TEMPLATES_DIR=str(templates),
            HM_HTTP_HOST="127.0.0.1",
            HM_HTTP_PORT=str(port),
            HM_REDIS_TYPE="memory",
        )
        process = subprocess.Popen(
            [sys.executable, str(ENTRYPOINT)],
            cwd=str(ENTRYPOINT.parent),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        wait_for_server(port, process)
        return process, f"http://127.0.0.1:{port}"

    processes = []

    def start(document):
        process, base_url = launch(document)
        processes.append(process)
        return base_url

    yield start
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def get(base_url, path):
    with urlopen(base_url + path, timeout=2) as response:
        return response.status, response.read().decode(), dict(response.headers)


def test_redis_commands_and_template_context(hmock):
    document = r'''
- key: state
  expect: {http: {method: GET, path: /state}}
  actions:
    - redis:
        - '{{ redisDo "SET" "greeting" "hello" }}'
        - '{{ redisDo "SET" "condition-key" "present" }}'
        - '{{ redisDo "RPUSH" "items" "one" }}'
        - '{{ redisDo "RPUSH" "items" "two" }}'
        - '{{ redisDo "LPUSH" "items" "zero" }}'
        - '{{ redisDo "HSET" "profile" "name" "Ada" }}'
        - '{{ redisDo "HSET" "profile" "role" "tester" }}'
    - reply_http:
        status_code: 200
        headers:
          X-Greeting: '{{ redisDo "GET" "greeting" }}'
          X-List: '{{ redisDo "LRANGE" "items" "0" "-1" }}'
          X-Hash: '{{ redisDo "HGETALL" "profile" }}'
        body: '{{ redisDo "HGET" "profile" "name" }}|{{ redisDo "LPOP" "items" }}|{{ redisDo "RPOP" "items" }}'
- key: keys
  expect: {http: {method: GET, path: /keys}}
  actions:
    - redis:
        - '{{ redisDo "SET" "temporary" "value" }}'
    - reply_http:
        status_code: 200
        body: '{{ redisDo "EXISTS" "temporary" }}|{{ redisDo "DEL" "temporary" }}|{{ redisDo "EXISTS" "temporary" }}|{{ redisDo "KEYS" "*" }}'
- key: condition
  expect:
    http: {method: GET, path: /conditional}
    condition: '{{ eq (redisDo "EXISTS" "condition-key") "1" }}'
  actions:
    - reply_http:
        status_code: 204
        body: should-not-be-used
'''
    base = hmock(document)

    status, body, headers = get(base, "/state")
    assert status == 200
    assert body == "Ada|zero|two"
    assert headers["X-Greeting"] == "hello"
    assert headers["X-List"] == "zero;;one;;two"
    assert headers["X-Hash"] == "name;;Ada;;role;;tester"

    status, body, _ = get(base, "/keys")
    assert status == 200
    assert body == "1|1|0|"

    # The condition can read state written by a previous request.
    status, _, _ = get(base, "/conditional")
    assert status == 204


def test_memory_redis_is_shared_between_requests_but_not_restarts(hmock):
    document = r'''
- key: write
  expect: {http: {method: POST, path: /write}}
  actions:
    - redis: ['{{ redisDo "SET" "survivor" "yes" }}']
    - reply_http: {status_code: 201, body: created}
- key: read
  expect: {http: {method: GET, path: /read}}
  actions:
    - reply_http: {status_code: 200, body: '{{ redisDo "GET" "survivor" }}'}
'''
    base = hmock(document)
    request = Request(base + "/write", method="POST")
    with urlopen(request, timeout=2) as response:
        assert response.status == 201
    assert get(base, "/read")[1] == "yes"

    # A fresh CLI process gets a fresh embedded store.
    second_base = hmock(document)
    assert get(second_base, "/read")[1] == "<no value>"


class CaptureHandler(BaseHTTPRequestHandler):
    records = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.__class__.records.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": self.rfile.read(length).decode(),
            }
        )
        self.send_response(500)
        self.end_headers()
        self.wfile.write(b"outbound failure")

    def log_message(self, *_):
        pass


@pytest.fixture
def capture_server():
    CaptureHandler.records = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_send_http_renders_request_and_ignores_outbound_failure(
    hmock, capture_server, tmp_path
):
    body_file = tmp_path / "outbound.txt"
    body_file.write_text("file-body", encoding="utf-8")
    outbound_port = capture_server.server_address[1]
    document = f'''
- key: outbound
  expect: {{http: {{method: POST, path: /trigger}}}}
  actions:
    - send_http:
        url: 'http://127.0.0.1:{outbound_port}/{{{{ .HTTPPath }}}}'
        method: POST
        headers:
          X-From-Path: '{{{{ .HTTPPath }}}}'
          X-From-Query: '{{{{ .HTTPQueryString }}}}'
        body: '{{{{ .HTTPBody }}}}'
    - send_http:
        url: 'http://127.0.0.1:{outbound_port}/file'
        method: POST
        body_from_file: {body_file.name}
    - reply_http:
        status_code: 202
        body: accepted
'''
    # body_from_file is resolved relative to the templates directory.
    # Place it there without relying on a repository path.
    (tmp_path / "templates" / body_file.name).write_text("file-body", encoding="utf-8")
    base = hmock(document)
    request = Request(
        base + "/trigger?x=1", data=b"request-body", method="POST",
        headers={"Content-Type": "text/plain"},
    )
    with urlopen(request, timeout=2) as response:
        assert response.status == 202
        assert response.read() == b"accepted"

    deadline = time.monotonic() + 2
    while len(CaptureHandler.records) < 2 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(CaptureHandler.records) == 2
    first, second = CaptureHandler.records
    assert first["path"] == "/trigger?x=1"
    assert first["headers"]["X-From-Path"] == "/trigger?x=1"
    assert first["headers"]["X-From-Query"] == "x=1"
    assert first["body"] == "request-body"
    assert second["path"] == "/file"
    assert second["body"] == "file-body"


def test_send_http_can_be_mixed_with_redis_sleep_and_reply(hmock, capture_server):
    outbound_port = capture_server.server_address[1]
    document = f'''
- key: mixed
  expect: {{http: {{method: PUT, path: /mixed}}}}
  actions:
    - redis: ['{{{{ redisDo "SET" "sequence" "redis-first" }}}}']
    - send_http:
        url: 'http://127.0.0.1:{outbound_port}/mixed'
        method: POST
        body: '{{{{ redisDo "GET" "sequence" }}}}'
    - sleep: {{duration: 1ms}}
    - reply_http:
        status_code: 200
        body: '{{{{ redisDo "GET" "sequence" }}}}'
'''
    base = hmock(document)
    request = Request(base + "/mixed", method="PUT")
    with urlopen(request, timeout=2) as response:
        assert response.status == 200
        assert response.read() == b"redis-first"
    deadline = time.monotonic() + 2
    while not CaptureHandler.records and time.monotonic() < deadline:
        time.sleep(0.01)
    assert CaptureHandler.records[0]["body"] == "redis-first"
