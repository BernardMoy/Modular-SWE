import pytest


def http_mock(**overrides):
    value = {
        "key": "evaluation-mock",
        "expect": {"http": {"method": "POST", "path": "/items/:id"}},
        "actions": [{"reply_http": {"status_code": 201, "body": "created"}}],
    }
    value.update(overrides)
    return value


def http_context(**overrides):
    value = {
        "http_context": {
            "method": "POST",
            "path": "/items/42",
            "body": "request",
            "headers": {"X-Request": "yes"},
            "query_string": "verbose=1",
        }
    }
    value["http_context"].update(overrides)
    return value


def test_http_match_renders_reply_and_merged_context(evaluate):
    mock = http_mock(
        expect={"http": {"method": "POST", "path": "/items/:id"}},
        actions=[
            {"reply_http": {"status_code": 201, "body": "{{ .HTTPPath }} {{ .HTTPBody }}"}}
        ],
    )
    status, result = evaluate({"mock": mock, "context": http_context()})
    assert status == 200
    assert result == {
        "expect_passed": True,
        "condition_passed": True,
        "condition_rendered": "",
        "actions_performed": [
            {
                "type": "reply_http_action_performed",
                "status_code": "201",
                "content_type": "application/json",
                "body": "/items/42 request",
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Length": "17",
                },
            }
        ],
    }


def test_match_failure_short_circuits_condition_and_actions(evaluate):
    mock = http_mock(
        expect={"http": {"method": "GET", "path": "/other"}},
        actions=[{"reply_http": {"status_code": 200, "body": "must not render"}}],
    )
    status, result = evaluate({"mock": mock, "context": http_context()})
    assert status == 200
    assert result == {"expect_passed": False, "actions_performed": []}


def test_failed_condition_returns_rendered_value_without_actions(evaluate):
    mock = http_mock(
        expect={
            "http": {"method": "POST", "path": "/items/:id"},
            "condition": "{{ false }}",
        }
    )
    status, result = evaluate({"mock": mock, "context": http_context()})
    assert status == 200
    assert result == {
        "expect_passed": True,
        "condition_passed": False,
        "condition_rendered": "false",
        "actions_performed": [],
    }


def test_actions_are_sorted_and_only_supported_dry_run_results_are_returned(evaluate):
    mock = http_mock(
        actions=[
            {"order": 5, "publish_amqp": {"exchange": "e", "routing_key": "r", "payload": "omit"}},
            {"order": 2, "publish_kafka": {"topic": "out", "payload": "{{ .HTTPBody }}"}},
            {"order": 4, "send_http": {"url": "http://127.0.0.1:1", "method": "POST"}},
            {"order": 1, "reply_http": {"status_code": 200, "body": "reply"}},
            {"order": 3, "sleep": {"duration": "1h"}},
            {"order": 0, "redis": ["SET", "key", "value"]},
        ]
    )
    status, result = evaluate({"mock": mock, "context": http_context()})
    assert status == 200
    assert [item["type"] for item in result["actions_performed"]] == [
        "reply_http_action_performed",
        "publish_kafka_action_performed",
    ]
    assert result["actions_performed"][0]["body"] == "reply"
    assert result["actions_performed"][1] == {
        "type": "publish_kafka_action_performed",
        "topic": "out",
        "payload": "request",
    }


@pytest.mark.parametrize(
    "expectation, context",
    [
        ({"kafka": {"topic": "events"}}, {"kafka_context": {"topic": "events", "payload": "p"}}),
        (
            {"amqp": {"exchange": "orders", "routing_key": "created"}},
            {"amqp_context": {"exchange": "orders", "routing_key": "created", "queue": "created", "payload": "p"}},
        ),
        (
            {"grpc": {"service": "pkg.Service", "method": "Get"}},
            {"grpc_context": {"service": "pkg.Service", "method": "Get", "payload": "{}", "headers": {}}},
        ),
    ],
)
def test_each_supported_channel_can_be_evaluated(evaluate, expectation, context):
    mock = {"key": "channel-mock", "expect": expectation, "actions": []}
    status, result = evaluate({"mock": mock, "context": context})
    assert status == 200
    assert result["expect_passed"] is True
    assert result["condition_passed"] is True
    assert result["actions_performed"] == []


def test_amqp_empty_queue_uses_routing_key(evaluate):
    mock = {"key": "amqp-fallback", "expect": {"amqp": {"exchange": "e", "routing_key": "rk", "queue": ""}}, "actions": []}
    context = {"amqp_context": {"exchange": "e", "routing_key": "rk", "payload": "p"}}
    status, result = evaluate({"mock": mock, "context": context})
    assert status == 200
    assert result["expect_passed"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"mock": http_mock(key=""), "context": http_context()},
        {"mock": http_mock(expect={}), "context": http_context()},
        {"mock": http_mock(expect={"grpc": {"service": "only"}}), "context": {}},
        {"mock": http_mock(expect={"kafka": {} }), "context": {"kafka_context": {"topic": "x", "payload": "p"}}},
        {"mock": http_mock(expect={"amqp": {"exchange": "e"}}), "context": {"amqp_context": {}}},
        {"mock": http_mock(), "context": []},
        {"mock": http_mock(), "context": {}},
        {"mock": http_mock(expect={"http": {"method": "POST", "path": "/x"}}), "context": {"kafka_context": {"topic": "x", "payload": "p"}}},
        {"mock": {"key": "x", "expect": {"http": {}, "kafka": {}}, "actions": []}, "context": http_context()},
    ],
)
def test_invalid_request_shapes_return_bad_request(evaluate, payload):
    status, _ = evaluate(payload)
    assert status == 400


def test_malformed_json_returns_bad_request(running_server):
    base, _ = running_server.start()
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen

    request = Request(
        base + "/api/v1/evaluate",
        data=b"not json",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(HTTPError) as error:
        urlopen(request, timeout=2)
    assert error.value.code == 400
