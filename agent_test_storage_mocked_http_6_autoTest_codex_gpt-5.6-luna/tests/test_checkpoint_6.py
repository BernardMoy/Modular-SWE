"""Black-box tests for checkpoint 6.

The tests communicate only with the hmock.py process and HTTP endpoints.  In
particular, they do not import modules from the implementation under test.
"""

import http.server
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import textwrap
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION_DIR = ROOT / ("implementation" if (ROOT / "implementation").exists() else "previous_implementation")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(url, method="GET", body=None, headers=None):
    req = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, dict(response.headers), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def write_yaml(directory, name, content):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def mock_server(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    http_port, admin_port = free_port(), free_port()
    env = os.environ.copy()
    env.update(
        {
            "HM_TEMPLATES_DIR": str(templates),
            "HM_HTTP_HOST": "127.0.0.1",
            "HM_HTTP_PORT": str(http_port),
            "HM_ADMIN_HTTP_HOST": "127.0.0.1",
            "HM_ADMIN_HTTP_PORT": str(admin_port),
            "HM_PERSISTENCE_PATH": str(tmp_path / "state.json"),
            "HM_REDIS_TYPE": "memory",
        }
    )
    process = subprocess.Popen(
        [sys.executable, "hmock.py"],
        cwd=str(IMPLEMENTATION_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    base = f"http://127.0.0.1:{http_port}"
    admin = f"http://127.0.0.1:{admin_port}"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read().decode(errors="replace")
            pytest.fail(f"hmock exited during startup: {stderr}")
        try:
            if request(admin + "/api/v1/health")[0] == 200:
                break
        except OSError:
            pass
        time.sleep(0.03)
    else:
        process.kill()
        pytest.fail("hmock did not become ready")
    yield templates, base, admin
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()


def behavior_yaml(key, path, action):
    action = textwrap.indent(textwrap.dedent(action).strip("\n"), " " * 8)
    return f"""- key: {key}
  expect:
    http:
      method: GET
      path: {path}
  actions:
    - reply_http:
{action}
"""


def launch_server(tmp_path, templates, **settings):
    http_port, admin_port = free_port(), free_port()
    env = os.environ.copy()
    env.update(
        {
            "HM_TEMPLATES_DIR": str(templates),
            "HM_HTTP_HOST": "127.0.0.1",
            "HM_HTTP_PORT": str(http_port),
            "HM_ADMIN_HTTP_HOST": "127.0.0.1",
            "HM_ADMIN_HTTP_PORT": str(admin_port),
            "HM_PERSISTENCE_PATH": str(tmp_path / "state.json"),
            "HM_REDIS_TYPE": "memory",
            **{key: str(value) for key, value in settings.items()},
        }
    )
    process = subprocess.Popen(
        [sys.executable, "hmock.py"],
        cwd=str(IMPLEMENTATION_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    admin = f"http://127.0.0.1:{admin_port}"
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(process.stderr.read().decode(errors="replace"))
        try:
            if request(admin + "/api/v1/health")[0] == 200:
                return process, f"http://127.0.0.1:{http_port}", admin
        except OSError:
            time.sleep(0.03)
    process.kill()
    pytest.fail("hmock did not become ready")


def test_hot_reload_default_sees_create_edit_and_delete(mock_server):
    templates, base, _ = mock_server
    target = templates / "dynamic.yaml"
    assert request(base + "/dynamic")[0] == 404
    write_yaml(templates, "dynamic.yaml", behavior_yaml("dynamic", "/dynamic", "      status_code: 200\n      body: first\n"))
    assert request(base + "/dynamic")[2] == b"first"
    write_yaml(templates, "dynamic.yaml", behavior_yaml("dynamic", "/dynamic", "      status_code: 200\n      body: second\n"))
    assert request(base + "/dynamic")[2] == b"second"
    target.unlink()
    assert request(base + "/dynamic")[0] == 404


def test_hot_reload_false_keeps_filesystem_snapshot(mock_server):
    templates = mock_server[0]
    write_yaml(templates, "frozen.yaml", behavior_yaml("frozen", "/frozen", "      status_code: 200\n      body: old\n"))
    process, base, _ = launch_server(mock_server[0].parent, templates, HM_TEMPLATES_DIR_HOT_RELOAD="false")
    try:
        assert request(base + "/frozen")[2] == b"old"
        write_yaml(templates, "frozen.yaml", behavior_yaml("frozen", "/frozen", "      status_code: 200\n      body: new\n"))
        assert request(base + "/frozen")[2] == b"old"
    finally:
        process.terminate()
        process.wait(timeout=2)


def test_cors_headers_apply_to_success_404_and_unmatched_options(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    write_yaml(templates, "cors.yaml", behavior_yaml("cors", "/cors", "      status_code: 201\n      headers:\n        Access-Control-Allow-Origin: mock-value\n      body: ok\n"))
    proc, base, _ = launch_server(tmp_path, templates, HM_CORS_ENABLED="true")
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                if request(base + "/cors")[0] == 201:
                    break
            except OSError:
                time.sleep(0.03)
        else:
            pytest.fail("server did not start")
        for path, method, expected in [("/cors", "GET", 201), ("/missing", "GET", 404), ("/missing", "OPTIONS", 200)]:
            status, headers, body = request(base + path, method)
            assert status == expected
            assert headers["Access-Control-Allow-Origin"] == ("mock-value" if path == "/cors" else "*")
            assert headers["Access-Control-Allow-Methods"] == "*"
            assert headers["Access-Control-Allow-Headers"] == "*"
            assert headers["Access-Control-Allow-Credentials"] == "true"
            if method == "OPTIONS":
                assert body == b""
    finally:
        proc.terminate()
        proc.wait(timeout=2)


def test_explicit_options_behavior_wins_over_cors_preflight(mock_server):
    templates = mock_server[0]
    write_yaml(templates, "options.yaml", """- key: options
  expect:
    http:
      method: OPTIONS
      path: /known
  actions:
    - reply_http:
        status_code: 200
        body: defined
""")
    process, base, _ = launch_server(templates.parent, templates, HM_CORS_ENABLED="true")
    try:
        assert request(base + "/known", "OPTIONS")[0] == 200
        assert request(base + "/known", "OPTIONS")[2] == b"defined"
    finally:
        process.terminate(); process.wait(timeout=2)


def test_reply_binary_is_raw_stable_and_has_size_and_disposition(mock_server):
    templates, base, _ = mock_server
    binary = templates / "payload.bin"
    binary.write_bytes(b"\x00\xff{{not-template}}\x80")
    write_yaml(templates, "binary.yaml", """- key: download
  expect:
    http:
      method: GET
      path: /download
  actions:
    - reply_http:
        status_code: 200
        body_from_binary_file: payload.bin
        binary_file_name: report.bin
""")
    status, headers, body = request(base + "/download")
    assert status == 200 and body == b"\x00\xff{{not-template}}\x80"
    assert headers["Content-Length"] == str(len(body))
    assert headers["Content-Disposition"] == 'inline; filename="report.bin"'
    binary.write_bytes(b"changed")
    assert request(base + "/download")[2] == b"\x00\xff{{not-template}}\x80"


def test_reply_binary_is_used_only_when_body_is_empty(mock_server):
    templates, base, _ = mock_server
    (templates / "x.bin").write_bytes(b"binary")
    write_yaml(templates, "body.yaml", """- key: empty
  expect: {http: {path: /empty}}
  actions:
    - reply_http:
        status_code: 200
        body: ""
        body_from_binary_file: x.bin
""" + """- key: text
  expect: {http: {path: /text}}
  actions:
    - reply_http:
        status_code: 200
        body: text
        body_from_binary_file: x.bin
""")
    assert request(base + "/empty")[2] == b"binary"
    assert request(base + "/text")[2] == b"text"


class CaptureHandler(http.server.BaseHTTPRequestHandler):
    captured = []
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.__class__.captured.append((dict(self.headers), self.rfile.read(length)))
        self.send_response(204)
        self.end_headers()
    def do_PUT(self):
        return self.do_POST()
    def log_message(self, *_):
        pass


def test_send_binary_post_is_multipart_and_non_post_is_raw(mock_server):
    templates, base, _ = mock_server
    (templates / "upload.bin").write_bytes(b"\x00\x01raw")
    receiver = http.server.ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
    threading.Thread(target=receiver.serve_forever, daemon=True).start()
    target = f"http://127.0.0.1:{receiver.server_port}"
    write_yaml(templates, "send.yaml", f"""- key: sender
  expect: {{http: {{path: /send}}}}
  actions:
    - send_http:
        url: {target}
        method: POST
        body_from_binary_file: upload.bin
        binary_file_name: chosen.bin
    - reply_http:
        status_code: 200
        body: done
""" + f"""- key: raw_sender
  expect: {{http: {{method: PUT, path: /send-raw}}}}
  actions:
    - send_http:
        url: {target}
        method: PUT
        body_from_binary_file: upload.bin
    - reply_http:
        status_code: 200
        body: done
""" + f"""- key: default_name
  expect: {{http: {{path: /default-name}}}}
  actions:
    - send_http:
        url: {target}
        method: POST
        headers:
          Content-Type: application/custom
        body_from_binary_file: upload.bin
    - reply_http:
        status_code: 200
        body: done
""")
    assert request(base + "/send")[0] == 200
    assert request(base + "/send-raw")[0] == 200
    assert request(base + "/default-name")[0] == 200
    receiver.shutdown()
    headers, body = CaptureHandler.captured[0]
    assert "multipart/form-data" in headers["Content-Type"]
    assert b'name="file"' in body and b'filename="chosen.bin"' in body and b"\x00\x01raw" in body
    raw_headers, raw_body = CaptureHandler.captured[1]
    assert raw_body == b"\x00\x01raw"
    default_headers, default_body = CaptureHandler.captured[2]
    assert default_headers["Content-Type"].startswith("multipart/form-data")
    assert b'filename="upload.bin"' in default_body and b"\x00\x01raw" in default_body


def test_omctl_push_and_delete_use_expected_urls_and_content_type(tmp_path):
    templates = tmp_path / "local"
    templates.mkdir()
    write_yaml(templates, "nested/item.yml", "- key: item\n  actions: []\n")
    received = []
    class AdminHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(("POST", self.path, dict(self.headers), self.rfile.read(int(self.headers.get("Content-Length", 0)))))
            self.send_response(200); self.end_headers()
        def do_DELETE(self):
            received.append(("DELETE", self.path, dict(self.headers), b""))
            self.send_response(204); self.end_headers()
        def log_message(self, *_): pass
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), AdminHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/root"
    try:
        command = [sys.executable, "hmock.py"]
        def run_cli(*args):
            try:
                return subprocess.run(command + list(args), cwd=IMPLEMENTATION_DIR, capture_output=True, text=True, timeout=3)
            except subprocess.TimeoutExpired:
                class TimedOut:
                    returncode = 124
                return TimedOut()
        push = run_cli("push", "-d", str(templates), "-u", url)
        assert push.returncode == 0
        assert received[-1][0:2] == ("POST", "/root/api/v1/templates")
        assert received[-1][2]["Content-Type"] == "application/yaml"
        assert b"key: item" in received[-1][3]
        push = run_cli("push", "--directory", str(templates), "--url", url, "--set-key", "staging")
        assert push.returncode == 0
        assert received[-1][0:2] == ("POST", "/root/api/v1/template_sets/staging")
        delete = run_cli("delete", "-u", url, "-k", "staging")
        assert delete.returncode == 0
        assert received[-1][0:2] == ("DELETE", "/root/api/v1/template_sets/staging")
    finally:
        server.shutdown()
