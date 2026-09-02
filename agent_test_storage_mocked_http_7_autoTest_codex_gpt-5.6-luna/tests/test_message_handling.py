"""Black-box acceptance tests for Kafka and AMQP support.

The tests start the documented ``hmock.py`` CLI and use only its HTTP admin
endpoint as an observation point.  They deliberately do not import the
implementation or rely on its module layout.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(process: subprocess.Popen, url: str) -> None:
    deadline = time.monotonic() + 4
    last_error = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stderr.read().decode(errors="replace")
            pytest.fail(f"hmock exited with {process.returncode}: {output}")
        try:
            with urlopen(url, timeout=0.25) as response:
                if response.status == 200:
                    return
        except (OSError, HTTPError) as exc:
            last_error = exc
        time.sleep(0.03)
    pytest.fail(f"hmock did not become healthy: {last_error}")


@pytest.fixture
def hmock_entrypoint() -> Path:
    """Use the implementation under test, with the baseline as the default."""
    selected = os.environ.get("HMOCK_IMPLEMENTATION", "previous_implementation")
    entrypoint = PROJECT_ROOT / selected / "hmock.py"
    if not entrypoint.is_file():
        pytest.fail(f"missing CLI entrypoint: {entrypoint}")
    return entrypoint


@pytest.fixture
def run_hmock(hmock_entrypoint, tmp_path):
    processes = []

    def run(
        definitions, *, extra_environment=None, files=None, expect_startup=True
    ):
        templates = tmp_path / f"templates-{len(processes)}"
        templates.mkdir()
        for name, contents in (files or {}).items():
            path = templates / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents, encoding="utf-8")
        (templates / "mocks.yaml").write_text(
            json.dumps(definitions), encoding="utf-8"
        )

        http_port = _free_port()
        admin_port = _free_port()
        environment = {
            "HM_TEMPLATES_DIR": str(templates),
            "HM_HTTP_HOST": "127.0.0.1",
            "HM_HTTP_PORT": str(http_port),
            "HM_ADMIN_HTTP_HOST": "127.0.0.1",
            "HM_ADMIN_HTTP_PORT": str(admin_port),
            "HM_PERSISTENCE_PATH": str(tmp_path / f"state-{len(processes)}.json"),
            "HM_REDIS_TYPE": "memory",
            "HM_ADMIN_HTTP_ENABLED": "true",
            "HM_KAFKA_ENABLED": "false",
            "HM_AMQP_ENABLED": "false",
        }
        environment.update(extra_environment or {})
        process = subprocess.Popen(
            [sys.executable, str(hmock_entrypoint)],
            cwd=hmock_entrypoint.parent,
            env={**os.environ, **environment},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes.append(process)
        if not expect_startup:
            deadline = time.monotonic() + 2
            while process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.03)
            if process.poll() is None:
                pytest.fail("hmock accepted an invalid message definition")
            return process
        _wait_for_health(process, f"http://127.0.0.1:{admin_port}/api/v1/health")
        return process

    yield run
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def test_kafka_expectation_is_accepted_and_service_starts(run_hmock):
    run_hmock(
        [
            {
                "key": "orders",
                "expect": {
                    "kafka": {"topic": "orders"},
                    "condition": ".KafkaPayload == \"ready\"",
                },
                "actions": [{"reply_http": {"status_code": 200, "body": "ok"}}],
            }
        ],
        extra_environment={"HM_KAFKA_ENABLED": "false"},
    )


@pytest.mark.parametrize(
    "action",
    [
        {"publish_kafka": {"topic": "orders", "payload": "{{ .KafkaPayload }}"}},
        {
            "publish_kafka": {
                "topic": "orders",
                "payload_from_file": "payload.txt",
            }
        },
    ],
)
def test_publish_kafka_forms_are_accepted(run_hmock, action):
    files = {"payload.txt": "payload from file: {{ .KafkaTopic }}"}
    definition = {
        "key": "publish-orders",
        "expect": {"kafka": {"topic": "orders"}},
        "actions": [
            action,
            {"reply_http": {"status_code": 202, "body": "published"}},
        ],
    }
    run_hmock([definition], files=files)


@pytest.mark.parametrize("queue", [None, ""])
def test_amqp_expectation_defaults_empty_queue_to_routing_key(run_hmock, queue):
    amqp = {"exchange": "events", "routing_key": "order.created"}
    if queue is not None:
        amqp["queue"] = queue
    run_hmock(
        [
            {
                "key": "created",
                "expect": {"amqp": amqp},
                "actions": [{"reply_http": {"status_code": 200, "body": "ok"}}],
            }
        ],
        extra_environment={"HM_AMQP_ENABLED": "false"},
    )


def test_publish_amqp_with_file_payload_is_accepted(run_hmock):
    run_hmock(
        [
            {
                "key": "publish-events",
                "expect": {
                    "amqp": {
                        "exchange": "events",
                        "routing_key": "order.created",
                        "queue": "orders",
                    }
                },
                "actions": [
                    {
                        "publish_amqp": {
                            "exchange": "events",
                            "routing_key": "order.created",
                            "payload_from_file": "event.txt",
                        }
                    },
                    {"reply_http": {"status_code": 202, "body": "published"}},
                ],
            }
        ],
        files={"event.txt": "{{ .AMQPQueue }}"},
    )


@pytest.mark.parametrize(
    "definition",
    [
        {
            "key": "missing-kafka-topic",
            "expect": {"kafka": {}},
            "actions": [{"reply_http": {"status_code": 200, "body": "ok"}}],
        },
        {
            "key": "missing-kafka-payload",
            "expect": {"http": {"path": "/publish"}},
            "actions": [
                {"publish_kafka": {"topic": "orders"}},
                {"reply_http": {"status_code": 200, "body": "ok"}},
            ],
        },
        {
            "key": "missing-amqp-routing-key",
            "expect": {
                "amqp": {"exchange": "events"},
            },
            "actions": [{"reply_http": {"status_code": 200, "body": "ok"}}],
        },
        {
            "key": "missing-amqp-payload",
            "expect": {"http": {"path": "/publish"}},
            "actions": [
                {
                    "publish_amqp": {
                        "exchange": "events",
                        "routing_key": "order.created",
                    }
                },
                {"reply_http": {"status_code": 200, "body": "ok"}},
            ],
        },
    ],
)
def test_required_message_fields_are_enforced(run_hmock, definition):
    run_hmock(
        [definition],
        extra_environment={
            "HM_KAFKA_ENABLED": "false",
            "HM_AMQP_ENABLED": "false",
        },
        expect_startup=False,
    )
