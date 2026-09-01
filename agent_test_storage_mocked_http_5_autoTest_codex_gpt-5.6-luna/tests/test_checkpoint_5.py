"""Black-box tests for checkpoint 5's HTTP API and persistence behaviour."""

import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _behavior(key, path, body):
    return {
        "key": key,
        "expect": {"http": {"method": "GET", "path": path}},
        "actions": [{"reply_http": {"status_code": 200, "body": body}}],
    }


def _request(url, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    request = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with urlopen(request, timeout=2) as response:
            return response.status, response.read(), dict(response.headers)
    except HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def _wait_for(url, process):
    deadline = time.monotonic() + 5
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stderr.read().decode(errors="replace")
            pytest.fail(f"hmock exited during startup: {output}")
        try:
            return _request(url)
        except (URLError, OSError) as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"server did not become ready: {last_error}")


@pytest.fixture
def server(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    baseline = _behavior("filesystem", "/filesystem", "file")
    (templates / "baseline.yaml").write_text(json.dumps([baseline]), encoding="utf-8")
    entrypoint = os.environ.get("HMOCK_ENTRYPOINT")
    if entrypoint is None:
        preferred = ROOT / "implementation" / "hmock.py"
        entrypoint = str(preferred if preferred.exists() else ROOT / "previous_implementation" / "hmock.py")

    http_port, admin_port = _free_port(), _free_port()
    env = os.environ.copy()
    env.update(
        {
            "HM_TEMPLATES_DIR": str(templates),
            "HM_HTTP_HOST": "127.0.0.1",
            "HM_HTTP_PORT": str(http_port),
            "HM_ADMIN_HTTP_HOST": "127.0.0.1",
            "HM_ADMIN_HTTP_PORT": str(admin_port),
            "HM_REDIS_TYPE": "memory",
        }
    )
    process = subprocess.Popen(
        [sys.executable, entrypoint],
        cwd=str(Path(entrypoint).resolve().parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    admin = f"http://127.0.0.1:{admin_port}"
    http = f"http://127.0.0.1:{http_port}"
    try:
        _wait_for(http + "/filesystem", process)
        yield admin, http, templates
    finally:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_health_endpoint(server):
    admin, _, _ = server
    status, body, _ = _request(admin + "/api/v1/health")
    assert status == 200
    assert json.loads(body) == {"status": "OK"}


def test_templates_lists_filesystem_and_api_mocks(server):
    admin, _, templates = server
    api_mock = _behavior("api-mock", "/from-api", "api")
    status, _, _ = _request(admin + "/api/v1/templates", "POST", [api_mock])
    assert status == 200
    status, body, _ = _request(admin + "/api/v1/templates")
    assert status == 200
    listed = json.loads(body)
    assert isinstance(listed, list)
    assert any(item.get("key") == "filesystem" for item in listed)
    assert any(item.get("key") == "api-mock" for item in listed)


def test_post_adds_mock_and_is_visible_to_main_server(server):
    admin, http, _ = server
    mock = _behavior("created", "/created", "created-body")
    status, body, _ = _request(admin + "/api/v1/templates", "POST", [mock])
    assert status == 200
    assert json.loads(body) == [mock]
    status, body, _ = _request(http + "/created")
    assert status == 200
    assert body == b"created-body"


def test_post_replaces_mock_with_same_key(server):
    admin, http, _ = server
    first = _behavior("replaceable", "/replace", "one")
    second = _behavior("replaceable", "/replace", "two")
    assert _request(admin + "/api/v1/templates", "POST", [first])[0] == 200
    assert _request(admin + "/api/v1/templates", "POST", [second])[0] == 200
    assert _request(http + "/replace")[1] == b"two"


def test_invalid_post_returns_bad_request(server):
    admin, _, _ = server
    status, body, _ = _request(admin + "/api/v1/templates", "POST", [{"key": "missing-actions"}])
    assert status == 400
    assert body


def test_delete_all_removes_only_api_mocks(server):
    admin, http, templates = server
    api_mock = _behavior("api", "/api", "api")
    assert _request(admin + "/api/v1/templates", "POST", [api_mock])[0] == 200
    assert _request(admin + "/api/v1/templates", "DELETE")[0] == 204
    assert _request(http + "/api")[0] == 404
    assert _request(http + "/filesystem")[0] == 200


def test_delete_one_distinguishes_missing_and_preserves_filesystem_collision(server):
    admin, http, templates = server
    filesystem_mock = _behavior("same-key", "/same", "filesystem")
    (templates / "filesystem.yaml").write_text(json.dumps([filesystem_mock]), encoding="utf-8")
    api_mock = _behavior("same-key", "/same", "api")
    assert _request(admin + "/api/v1/templates", "POST", [api_mock])[0] == 200
    assert _request(admin + "/api/v1/templates/same-key", "DELETE")[0] == 204
    assert _request(http + "/same")[1] == b"filesystem"
    assert _request(admin + "/api/v1/templates/same-key", "DELETE")[0] == 404


def test_template_sets_are_replaceable_and_isolated(server):
    admin, http, _ = server
    set_a = _behavior("a", "/a", "a")
    set_b = _behavior("b", "/b", "b")
    replacement = _behavior("a2", "/a2", "a2")
    assert _request(admin + "/api/v1/template_sets/alpha", "POST", [set_a])[0] == 200
    assert _request(admin + "/api/v1/template_sets/beta", "POST", [set_b])[0] == 200
    assert _request(http + "/a")[0] == 200
    assert _request(http + "/b")[0] == 200
    assert _request(admin + "/api/v1/template_sets/alpha", "POST", [replacement])[0] == 200
    assert _request(http + "/a")[0] == 404
    assert _request(http + "/a2")[0] == 200
    assert _request(admin + "/api/v1/template_sets/alpha", "DELETE")[0] == 204
    assert _request(http + "/b")[0] == 200
    assert _request(http + "/a2")[0] == 404


def test_api_mocks_survive_process_restart(server):
    admin, http, templates = server
    mock = _behavior("persistent", "/persistent", "still-here")
    assert _request(admin + "/api/v1/templates", "POST", [mock])[0] == 200
    # The server fixture's temporary directory is the persistence boundary.  Restarting
    # is performed by launching the same CLI with the same directory and ports.
    entrypoint = os.environ.get("HMOCK_ENTRYPOINT", str(ROOT / "previous_implementation" / "hmock.py"))
    http_port, admin_port = int(http.rsplit(":", 1)[1]), int(admin.rsplit(":", 1)[1])
    env = os.environ.copy()
    env.update({"HM_TEMPLATES_DIR": str(templates), "HM_HTTP_HOST": "127.0.0.1", "HM_HTTP_PORT": str(http_port), "HM_ADMIN_HTTP_HOST": "127.0.0.1", "HM_ADMIN_HTTP_PORT": str(admin_port), "HM_REDIS_TYPE": "memory"})
    # Stop the fixture-owned process indirectly by making the persistence assertion
    # through a fresh CLI process on new ports; the original remains untouched.
    fresh_admin, fresh_http = _free_port(), _free_port()
    env.update({"HM_HTTP_PORT": str(fresh_http), "HM_ADMIN_HTTP_PORT": str(fresh_admin)})
    process = subprocess.Popen([sys.executable, entrypoint], cwd=str(Path(entrypoint).resolve().parent), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        _wait_for(f"http://127.0.0.1:{fresh_admin}/api/v1/health", process)
        assert _request(f"http://127.0.0.1:{fresh_http}/persistent")[1] == b"still-here"
    finally:
        process.terminate()
        process.wait(timeout=3)


def test_reserved_internal_redis_key_is_rejected(server):
    admin, http, _ = server
    mock = _behavior("reserved", "/reserved", '{{ redisDo "GET" "__hmock_internal:templates" }}')
    assert _request(admin + "/api/v1/templates", "POST", [mock])[0] == 200
    status, body, _ = _request(http + "/reserved")
    assert status >= 400
    assert body


def test_admin_server_can_be_disabled(tmp_path):
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "baseline.yaml").write_text(
        json.dumps([_behavior("filesystem", "/filesystem", "file")]), encoding="utf-8"
    )
    entrypoint = os.environ.get("HMOCK_ENTRYPOINT")
    if entrypoint is None:
        preferred = ROOT / "implementation" / "hmock.py"
        entrypoint = str(preferred if preferred.exists() else ROOT / "previous_implementation" / "hmock.py")
    main_port, admin_port = _free_port(), _free_port()
    env = os.environ.copy()
    env.update(
        {
            "HM_TEMPLATES_DIR": str(templates),
            "HM_HTTP_HOST": "127.0.0.1",
            "HM_HTTP_PORT": str(main_port),
            "HM_ADMIN_HTTP_ENABLED": "false",
            "HM_ADMIN_HTTP_HOST": "127.0.0.1",
            "HM_ADMIN_HTTP_PORT": str(admin_port),
            "HM_REDIS_TYPE": "memory",
        }
    )
    process = subprocess.Popen(
        [sys.executable, entrypoint],
        cwd=str(Path(entrypoint).resolve().parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for(f"http://127.0.0.1:{main_port}/filesystem", process)
        with pytest.raises(URLError):
            urlopen(f"http://127.0.0.1:{admin_port}/api/v1/health", timeout=1)
    finally:
        process.terminate()
        process.wait(timeout=3)
