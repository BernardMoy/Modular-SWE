"""Black-box tests for checkpoint 2.

The server is started as the documented CLI entrypoint and is exercised over
HTTP.  Temporary directories are used for every template and response file.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import pytest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = next(
    (candidate / "hmock.py"
     for candidate in (ROOT / "implementation", ROOT / "previous_implementation")
     if (candidate / "hmock.py").is_file()),
    ROOT / "previous_implementation" / "hmock.py",
)


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _write_behavior(directory, body, *, headers=None, body_from_file=None):
    # YAML quoting is deliberately avoided for the body: all test bodies are
    # valid block scalars, and this also keeps template punctuation literal.
    header_yaml = "{}"
    if headers:
        header_yaml = "\n" + "\n".join(
            f"          {key}: '{value}'" for key, value in headers.items()
        )
    file_field = ""
    if body_from_file is not None:
        file_field = f"\n        body_from_file: '{body_from_file}'"
    (directory / "behavior.yaml").write_text(
        "- key: checkpoint\n"
        "  expect:\n"
        "    http:\n"
        "      method: GET\n"
        "      path: /check\n"
        "  actions:\n"
        "    - reply_http:\n"
        "        status_code: 200\n"
        f"        headers: {header_yaml}\n"
        "        body: |-\n"
        + "          " + body.replace("\n", "\n          ")
        + file_field
        + "\n",
        encoding="utf-8",
    )


class RunningServer:
    def __init__(self, templates):
        self.templates = templates
        self.port = _free_port()
        env = os.environ.copy()
        env.update(
            HM_TEMPLATES_DIR=str(templates),
            HM_HTTP_HOST="127.0.0.1",
            HM_HTTP_PORT=str(self.port),
        )
        self.process = subprocess.Popen(
            [sys.executable, str(ENTRYPOINT)],
            cwd=str(ENTRYPOINT.parent),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def __enter__(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                stderr = self.process.stderr.read()
                raise AssertionError(f"hmock exited during startup: {stderr}")
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.1):
                    return self
            except OSError:
                time.sleep(0.02)
        raise AssertionError("hmock did not start listening")

    def __exit__(self, *_):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)

    def request(self, path="/check", headers=None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}", headers=headers or {}
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, dict(response.headers.items()), response.read()


@pytest.fixture
def server(tmp_path):
    def start(body, **kwargs):
        _write_behavior(tmp_path, body, **kwargs)
        return RunningServer(tmp_path)

    return start


def test_json_path_helpers_cover_matches_and_empty_or_missing_values(server):
    body = (
        '{{jsonPath "foo" .HTTPBody}}|{{jsonPath "//bar" .HTTPBody}}|'
        '{{jsonPath "missing" .HTTPBody}}|{{jsonPath "foo" ""}}'
    )
    with server(body) as app:
        # XPath-style JSON queries operate on JSON, not the request path.
        request = urllib.request.Request(
            f"http://127.0.0.1:{app.port}/check",
            data=b'{"foo":"one","nested":{"bar":"two"}}',
            method="GET",
        )
        # The behavior is GET; sending a body is intentional and supported by
        # the CLI's request context.
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.read().decode() == "one|two||"


def test_gjson_path_supports_nested_fields_indexes_wildcard_count_and_missing(server):
    body = (
        '{{gJsonPath "context.type" .HTTPBody}}|'
        '{{gJsonPath "users.1.name" .HTTPBody}}|'
        '{{gJsonPath "items.0.id" .HTTPBody}}|'
        '{{len (gJsonPath "items.#.id" .HTTPBody)}}|'
        '{{gJsonPath "items.#" .HTTPBody}}|'
        '{{gJsonPath "absent.value" .HTTPBody}}|{{gJsonPath "x" ""}}'
    )
    with server(body) as app:
        request = urllib.request.Request(
            f"http://127.0.0.1:{app.port}/check",
            data=json.dumps({
                "context": {"type": "demo"},
                "users": [{"name": "first"}, {"name": "second"}],
                "items": [{"id": "a"}, {"id": "b"}],
            }).encode(),
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            assert response.read().decode() == "demo|second|a|2|2||"


def test_gjson_path_invalid_json_is_a_render_failure(server):
    with server('{{gJsonPath "x" .HTTPBody}}') as app:
        request = urllib.request.Request(
            f"http://127.0.0.1:{app.port}/check", data=b"not-json"
        )
        with pytest.raises((urllib.error.URLError, ConnectionError)):
            urllib.request.urlopen(request, timeout=3)


def test_uuidv5_is_deterministic_and_uses_oid_namespace(server):
    with server('{{uuidv5 "same input"}}') as app:
        first = app.request()[2]
        second = app.request()[2]
    assert first == second
    # This is the externally specified OID namespace and makes the namespace
    # requirement observable without relying on implementation internals.
    import uuid

    assert first.decode() == str(uuid.uuid5(uuid.NAMESPACE_OID, "same input"))


def test_regex_helpers_return_full_match_groups_and_first_group_edge_cases(server):
    body = (
        '{{len (regexFindAllSubmatch "(ab)([0-9]+)" "xxab42yy")}}|'
        '{{index (regexFindAllSubmatch "(ab)([0-9]+)" "xxab42yy") 0}}|'
        '{{index (regexFindAllSubmatch "(ab)([0-9]+)" "xxab42yy") 2}}|'
        '{{regexFindFirstSubmatch "(ab)([0-9]+)" "xxab42yy"}}|'
        '{{regexFindFirstSubmatch "ab" "xxabyy"}}|'
        '{{regexFindFirstSubmatch "(zz)" "xxabyy"}}'
    )
    with server(body) as app:
        assert app.request()[2].decode() == "3|ab42|42|ab|||"


def test_hmac_html_escape_and_last_index_helpers(server):
    body = (
        '{{hmacSHA256 "secret" "message"}}|'
        '{{htmlEscapeString "<a & \\"q\\" \'x\'>"}}|'
        '{{isLastIndex 1 "ab"}}|{{isLastIndex 0 "ab"}}|'
        '{{isLastIndex 0 ""}}'
    )
    with server(body) as app:
        result = app.request()[2].decode()
    expected_hmac = hmac.new(b"secret", b"message", hashlib.sha256).hexdigest()
    assert result == expected_hmac + '|&lt;a &amp; &#34;q&#34; &#39;x&#39;&gt;|true|false|false'


def test_file_body_is_relative_to_templates_dir_and_rendered_with_request_context(server, tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "body.txt").write_text("Hello {{.HTTPHeader.Get \"X-Name\"}}", encoding="utf-8")
    with server("", body_from_file="nested/body.txt") as app:
        assert app.request(headers={"X-Name": "Ada"})[2] == b"Hello Ada"


def test_file_body_is_a_snapshot_and_inline_body_takes_precedence(server, tmp_path):
    body_file = tmp_path / "body.txt"
    body_file.write_text("from file", encoding="utf-8")
    with server("inline", body_from_file="body.txt") as app:
        body_file.write_text("changed", encoding="utf-8")
        assert app.request()[2] == b"inline"


def test_empty_inline_body_uses_file_body(server, tmp_path):
    body_file = tmp_path / "body.txt"
    body_file.write_text("from file", encoding="utf-8")
    with server("", body_from_file="body.txt") as app:
        body_file.write_text("changed after load", encoding="utf-8")
        assert app.request()[2] == b"from file"


def test_every_templated_header_value_is_rendered(server):
    with server("ok", headers={"X-Request-Name": "{{.HTTPHeader.Get \"X-Name\"}}"}) as app:
        _, headers, body = app.request(headers={"X-Name": "Ada"})
    assert body == b"ok"
    assert headers["X-Request-Name"] == "Ada"
