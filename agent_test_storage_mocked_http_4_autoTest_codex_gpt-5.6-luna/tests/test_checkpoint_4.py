import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _write_definitions(directory, text):
    directory.mkdir()
    (directory / "definitions.yaml").write_text(text, encoding="utf-8")


def _get(port, path="/"):
    try:
        response = urlopen(f"http://127.0.0.1:{port}{path}", timeout=2)
    except HTTPError as exc:
        return exc.code, exc.read().decode()
    return response.status, response.read().decode()


@pytest.fixture
def cli_server(tmp_path, hmock_entrypoint):
    processes = []

    def start(definitions):
        templates = tmp_path / f"templates-{len(processes)}"
        _write_definitions(templates, definitions)
        port = _free_port()
        environment = os.environ.copy()
        environment.update(
            HM_TEMPLATES_DIR=str(templates),
            HM_HTTP_HOST="127.0.0.1",
            HM_HTTP_PORT=str(port),
            HM_REDIS_TYPE="memory",
        )
        process = subprocess.Popen(
            [sys.executable, str(hmock_entrypoint)],
            cwd=str(hmock_entrypoint.parent),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append(process)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                raise AssertionError(
                    f"CLI exited during startup ({process.returncode}): {stdout}{stderr}"
                )
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    return port
            except OSError:
                time.sleep(0.02)
        process.kill()
        raise AssertionError("CLI did not start")

    yield start
    for process in processes:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def _assert_startup_rejected(tmp_path, hmock_entrypoint, definitions):
    templates = tmp_path / "invalid-definitions"
    _write_definitions(templates, definitions)
    environment = os.environ.copy()
    environment.update(
        HM_TEMPLATES_DIR=str(templates),
        HM_HTTP_HOST="127.0.0.1",
        HM_HTTP_PORT=str(_free_port()),
        HM_REDIS_TYPE="memory",
    )
    process = subprocess.Popen(
        [sys.executable, str(hmock_entrypoint)],
        cwd=str(hmock_entrypoint.parent),
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        result = process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=2)
        pytest.fail("CLI accepted invalid definitions and continued serving")
    assert result != 0


def test_all_three_kinds_are_accepted_and_abstract_behavior_does_not_match(cli_server):
    port = cli_server(
        """
- key: reusable
  kind: Template
  template: '{{.color}}'
- key: base
  kind: AbstractBehavior
  expect: {http: {method: GET, path: /abstract}}
  actions: [{reply_http: {status_code: 201, body: inherited}}]
- key: concrete
  kind: Behavior
  extend: base
  values: {color: blue}
  expect: {http: {path: /item}}
"""
    )
    assert _get(port, "/abstract") == (404, "not found")
    assert _get(port, "/item") == (201, "inherited")


def test_template_reference_supports_request_context_and_values(cli_server):
    port = cli_server(
        """
- key: request-json
  kind: Template
  template: '{"path":"{{.HTTPPath}}","body":"{{.HTTPBody}}"}'
- key: item
  kind: Behavior
  values: {color: purple}
  expect: {http: {method: GET, path: /item}}
  actions:
    - reply_http:
        status_code: 200
        body: '{{template "request-json" .}}'
"""
    )
    # The template receives the request context, including path and body.
    request = Request("http://127.0.0.1:%s/item" % port, data=b"hello", method="GET")
    with urlopen(request, timeout=2) as response:
        assert json.loads(response.read().decode()) == {"path": "/item", "body": "hello"}


def test_template_can_receive_values_context(cli_server):
    port = cli_server(
        """
- key: color
  kind: Template
  template: '{{.color}}'
- key: item
  kind: Behavior
  values: {color: purple}
  expect: {http: {method: GET, path: /item}}
  actions: [{reply_http: {status_code: 200, body: '{{template "color" .Values}}'}}]
"""
    )
    assert _get(port, "/item") == (200, "purple")


@pytest.mark.parametrize("kind", ["Unknown", "", "behavior", "template"])
def test_unknown_kind_is_rejected(tmp_path, hmock_entrypoint, kind):
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        f"- key: x\n  kind: {kind!r}\n  actions: [{{reply_http: {{status_code: 200, body: ok}}}}]\n",
    )


@pytest.mark.parametrize("field", ["expect", "actions", "values"])
def test_template_rejects_behavior_fields(tmp_path, hmock_entrypoint, field):
    value = {"expect": "{http: {method: GET, path: /x}}", "actions": "[]", "values": "{x: y}"}[field]
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        f"- key: x\n  kind: Template\n  template: x\n  {field}: {value}\n",
    )


def test_behavior_cannot_define_template(tmp_path, hmock_entrypoint):
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        "- key: x\n  kind: Behavior\n  template: x\n  actions: [{reply_http: {status_code: 200, body: ok}}]\n",
    )


@pytest.mark.parametrize("kind,extra", [
    ("Behavior", "actions: [{reply_http: {status_code: 200, body: ok}}]"),
    ("AbstractBehavior", "actions: [{reply_http: {status_code: 200, body: ok}}]"),
    ("Template", "template: x"),
])
def test_each_kind_rejects_fields_outside_its_allowed_schema(
    tmp_path, hmock_entrypoint, kind, extra
):
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        f"- key: x\n  kind: {kind}\n  {extra}\n  unexpected: value\n",
    )


def test_abstract_behavior_cannot_define_extend(tmp_path, hmock_entrypoint):
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        "- key: x\n  kind: AbstractBehavior\n  extend: y\n  actions: [{reply_http: {status_code: 200, body: ok}}]\n",
    )


def test_template_requires_a_template_body(tmp_path, hmock_entrypoint):
    _assert_startup_rejected(
        tmp_path, hmock_entrypoint, "- key: x\n  kind: Template\n"
    )


@pytest.mark.parametrize("definition", [
    "- kind: Template\n  template: x\n",
    "- key: '   '\n  kind: Template\n  template: x\n",
])
def test_every_kind_requires_non_empty_key(tmp_path, hmock_entrypoint, definition):
    _assert_startup_rejected(tmp_path, hmock_entrypoint, definition)


def test_missing_parent_is_skipped_and_child_is_loaded_on_its_own(cli_server):
    port = cli_server(
        """
- key: child
  kind: Behavior
  extend: absent
  expect: {http: {method: GET, path: /child}}
  actions: [{reply_http: {status_code: 202, body: child}}]
"""
    )
    assert _get(port, "/child") == (202, "child")


def test_definition_order_does_not_affect_inheritance_and_values_are_merged(cli_server):
    port = cli_server(
        """
- key: child
  kind: Behavior
  extend: base
  values: {color: purple, size: large}
- key: base
  kind: AbstractBehavior
  values: {color: blue, shape: round}
  expect: {http: {method: GET, path: /base}}
  actions: [{reply_http: {status_code: 200, body: '{{.Values.color}}/{{.Values.shape}}/{{.Values.size}}'}}]
"""
    )
    assert _get(port, "/base") == (200, "purple/round/large")


def test_recursive_expectation_merge_preserves_parent_fields(cli_server):
    port = cli_server(
        """
- key: base
  kind: AbstractBehavior
  expect: {http: {method: GET, path: /base}, condition: 'true'}
  actions: [{reply_http: {status_code: 200, body: ok}}]
- key: child
  kind: Behavior
  extend: base
  expect: {http: {path: /child}}
"""
    )
    assert _get(port, "/child") == (200, "ok")


def test_inherited_actions_are_sorted_with_negative_and_default_orders(cli_server):
    events = []

    class Capture(BaseHTTPRequestHandler):
        def do_POST(self):
            events.append((self.path, time.monotonic()))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_):
            pass

    capture_server = ThreadingHTTPServer(("127.0.0.1", 0), Capture)
    threading.Thread(target=capture_server.serve_forever, daemon=True).start()
    try:
        capture_url = f"http://127.0.0.1:{capture_server.server_port}"
        port = cli_server(
            f"""
- key: base
  kind: AbstractBehavior
  expect: {{http: {{method: GET, path: /ordered}}}}
  actions:
    - order: 0
      send_http: {{url: {capture_url}/base, method: POST}}
    - reply_http: {{status_code: 200, body: done}}
- key: child
  kind: Behavior
  extend: base
  actions:
    - order: -100
      sleep: {{duration: 150ms}}
    - order: 0
      send_http: {{url: {capture_url}/child, method: POST}}
"""
        )
        started = time.monotonic()
        assert _get(port, "/ordered") == (200, "done")
        assert events and events[0][1] - started >= 0.12
        assert [path for path, _ in events] == ["/base", "/child"]
    finally:
        capture_server.shutdown()
        capture_server.server_close()


def test_multiple_reply_actions_are_rejected(tmp_path, hmock_entrypoint):
    _assert_startup_rejected(
        tmp_path,
        hmock_entrypoint,
        """
- key: x
  kind: Behavior
  actions:
    - reply_http: {status_code: 200, body: one}
    - reply_http: {status_code: 201, body: two}
""",
    )
