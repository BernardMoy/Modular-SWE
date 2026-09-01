"""Black-box acceptance tests for the HTTP-only hmock checkpoint."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from http.client import HTTPConnection
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "hmock.py"


def write_yaml(directory: Path, name: str, content: str) -> None:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_port(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError("hmock exited during startup")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=.1):
                return
        except OSError:
            time.sleep(.02)
    raise AssertionError("hmock did not start listening")


@pytest.fixture
def hmock(tmp_path: Path):
    templates = tmp_path / "templates"
    templates.mkdir()
    processes = []

    def launch(log_level="info"):
        port = free_port()
        env = os.environ.copy()
        env.update(HM_TEMPLATES_DIR=str(templates), HM_HTTP_PORT=str(port), HM_HTTP_HOST="127.0.0.1", HM_LOG_LEVEL=log_level)
        process = subprocess.Popen([sys.executable, str(ENTRYPOINT)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        processes.append(process)
        wait_for_port(port, process)

        def request(method, path, body="", headers=None):
            connection = HTTPConnection("127.0.0.1", port, timeout=3)
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            result = response.status, dict(response.getheaders()), response.read()
            connection.close()
            return result

        return request, process

    yield templates, launch
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def reply(key, path, body="ok", method="GET", condition=None, extra=""):
    condition_line = f"    condition: {condition!r}\n" if condition is not None else ""
    return f"""- key: {key}
  kind: Behavior
  expect:
    http: {{method: {method}, path: {path}}}
{condition_line}  actions:
    - reply_http:
        status_code: 200
        body: {body!r}
{extra}"""


def test_response_defaults_and_explicit_headers(hmock):
    templates, launch = hmock
    write_yaml(templates, "basic.yml", reply("basic", "/ping", "OK"))
    write_yaml(templates, "text.yaml", reply("text", "/text", "hello", extra="        headers: {Content-Type: text/plain}\n"))
    request, _ = launch()
    status, headers, body = request("GET", "/ping")
    assert (status, body, headers["Content-Type"], headers["Content-Length"]) == (200, b"OK", "application/json", "2")
    status, headers, body = request("GET", "/text")
    assert (status, body, headers["Content-Type"], headers["Content-Length"]) == (200, b"hello", "text/plain", "5")


def test_method_and_path_must_match(hmock):
    templates, launch = hmock
    write_yaml(templates, "route.yml", reply("r", "/only", "found"))
    request, _ = launch()
    assert request("POST", "/only")[2] == b"not found"
    assert request("GET", "/missing")[2] == b"not found"


def test_named_path_and_request_context(hmock):
    templates, launch = hmock
    write_yaml(templates, "route.yml", reply("r", "/users/:id", '{{ index (split .HTTPPath "/") 2 }}'))
    request, _ = launch()
    assert request("GET", "/users/42?x=1")[2] == b"42"


def test_body_headers_query_and_condition_context(hmock):
    templates, launch = hmock
    write_yaml(templates, "context.yml", """- key: context
  expect:
    http: {method: POST, path: /inspect}
    condition: '{{.HTTPHeader.Get "X-Token" | eq "yes"}}'
  actions:
    - reply_http:
        status_code: 201
        headers: {X-Seen: '{{.HTTPQueryString}}'}
        body: '{{.HTTPBody}}'
""")
    request, _ = launch()
    status, headers, body = request("POST", "/inspect?a=1", "raw", {"X-Token": "yes"})
    assert (status, headers["X-Seen"], body) == (201, "a=1", b"raw")
    assert request("POST", "/inspect", "raw", {"X-Token": "no"})[2] == b"not found"


@pytest.mark.parametrize("condition", ["{{ `true` }}", "{{ print \"true\" }}"])
def test_condition_requires_exact_rendered_true(hmock, condition):
    templates, launch = hmock
    write_yaml(templates, "condition.yml", reply("c", "/c", "matched", condition=condition))
    assert launch()[0]("GET", "/c")[2] == b"matched"


def test_missing_empty_and_failed_conditions(hmock):
    templates, launch = hmock
    write_yaml(templates, "conditions.yml", """- key: empty
  expect: {http: {method: GET, path: /c}}
  actions: [{reply_http: {status_code: 200, body: pass}}]
- key: failed
  expect:
    http: {method: GET, path: /c}
    condition: '{{.UndefinedValue}}'
  actions: [{reply_http: {status_code: 200, body: no}}]
""")
    assert launch()[0]("GET", "/c")[2] == b"pass"


def test_recursive_yaml_loading_and_other_extensions_ignored(hmock):
    templates, launch = hmock
    write_yaml(templates, "a/deep.yaml", reply("a", "/deep", "yes"))
    write_yaml(templates, "a/also.yml", reply("b", "/also", "also"))
    write_yaml(templates, "ignored.txt", reply("b", "/ignored", "no"))
    request, _ = launch()
    assert request("GET", "/deep")[2] == b"yes"
    assert request("GET", "/also")[2] == b"also"
    assert request("GET", "/ignored")[2] == b"not found"


def test_kind_defaults_to_behavior(hmock):
    templates, launch = hmock
    write_yaml(templates, "default-kind.yml", """- key: default-kind
  expect: {http: {method: GET, path: /default-kind}}
  actions: [{reply_http: {status_code: 200, body: works}}]
""")
    assert launch()[0]("GET", "/default-kind")[2] == b"works"


def test_load_order_first_passing_behavior_wins_and_sleep_runs(hmock):
    templates, launch = hmock
    write_yaml(templates, "01.yml", """- key: first
  expect: {http: {method: GET, path: /order}}
  actions:
    - sleep: {duration: 10ms}
    - reply_http: {status_code: 202, body: first}
- key: second
  expect: {http: {method: GET, path: /order}}
  actions: [{reply_http: {status_code: 200, body: second}}]
""")
    start = time.monotonic()
    status, _, body = launch()[0]("GET", "/order")
    assert (status, body) == (202, b"first")
    assert time.monotonic() - start >= .008


def test_sleep_accepts_all_declared_duration_units(hmock):
    templates, launch = hmock
    write_yaml(templates, "units.yml", """- key: units
  expect: {http: {method: GET, path: /units}}
  actions:
    - sleep: {duration: 0ns}
    - sleep: {duration: 0us}
    - sleep: {duration: 0ms}
    - sleep: {duration: 0s}
    - sleep: {duration: 0m}
    - sleep: {duration: 0h}
    - reply_http: {status_code: 200, body: units}
""")
    assert launch()[0]("GET", "/units")[2] == b"units"


def test_duplicate_key_warns_in_structured_json(hmock):
    templates, launch = hmock
    write_yaml(templates, "01.yml", reply("same", "/one", "first"))
    write_yaml(templates, "02.yml", reply("same", "/two", "last"))
    request, process = launch("warn")
    assert request("GET", "/two")[2] == b"last"
    process.terminate()
    records = [json.loads(line) for line in process.communicate(timeout=2)[0].splitlines() if line.strip()]
    assert any(record.get("level") == "warn" and "same" in json.dumps(record) for record in records)


@pytest.mark.parametrize("bad", [
    "- expect: {http: {method: GET, path: /bad}}\n  actions: [{reply_http: {status_code: 200}}]\n",
    "- key: ''\n  expect: {http: {method: GET, path: /bad}}\n  actions: [{reply_http: {status_code: 200}}]\n",
    "- key: 123\n  expect: {http: {method: GET, path: /bad}}\n  actions: [{reply_http: {status_code: 200}}]\n",
])
def test_invalid_key_is_rejected(tmp_path, bad):
    templates = tmp_path / "templates"
    templates.mkdir()
    write_yaml(templates, "bad.yml", bad)
    env = os.environ.copy()
    env.update(HM_TEMPLATES_DIR=str(templates), HM_HTTP_PORT=str(free_port()), HM_HTTP_HOST="127.0.0.1")
    result = subprocess.run([sys.executable, str(ENTRYPOINT)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=3)
    assert result.returncode != 0


def test_multiple_reply_actions_are_rejected(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    write_yaml(templates, "bad.yml", """- key: twice
  expect: {http: {method: GET, path: /bad}}
  actions:
    - reply_http: {status_code: 200}
    - reply_http: {status_code: 201}
""")
    env = os.environ.copy()
    env.update(HM_TEMPLATES_DIR=str(templates), HM_HTTP_PORT=str(free_port()), HM_HTTP_HOST="127.0.0.1")
    result = subprocess.run([sys.executable, str(ENTRYPOINT)], cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=3)
    assert result.returncode != 0


def test_log_record_contains_required_request_response_fields(hmock):
    templates, launch = hmock
    write_yaml(templates, "log.yml", reply("log", "/logged", "ok"))
    request, process = launch("info")
    assert request("GET", "/logged")[0] == 200
    process.terminate()
    records = [json.loads(line) for line in process.communicate(timeout=2)[0].splitlines() if line.strip()]
    assert any(all(field in record for field in ("http_path", "http_method", "http_host", "http_req", "http_res")) for record in records)


def test_error_log_level_suppresses_info_request_records(hmock):
    templates, launch = hmock
    write_yaml(templates, "log.yml", reply("log", "/logged", "ok"))
    request, process = launch("error")
    assert request("GET", "/logged")[0] == 200
    process.terminate()
    output = process.communicate(timeout=2)[0]
    assert not any("http_path" in line for line in output.splitlines())
