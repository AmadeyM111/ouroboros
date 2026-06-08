import asyncio
import importlib
import io
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


class FakeWebSocket:
    def __init__(self, messages=None, headers=None):
        self._messages = list(messages or [])
        self.sent = []
        self.closed = None
        self.request_headers = headers
        self.remote_address = ("127.0.0.1", 12345)

    async def send(self, message):
        self.sent.append(message)

    async def close(self, code=None, reason=None):
        self.closed = (code, reason)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)


class FakeAgentConnection:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def send(self, message):
        self.sent.append(message)

    async def recv(self):
        if not self.messages:
            await asyncio.sleep(0)
            raise TimeoutError("no more messages")
        return self.messages.pop(0)


class WsAnalyticsServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.pop("ws_analytics_service", None)
        cls.service = importlib.import_module("ws_analytics_service")

    def make_config(self, **overrides):
        values = {
            "listen_host": "127.0.0.1",
            "listen_port": 8787,
            "agent_url": "ws://agent.local/ws",
            "inbound_token": None,
            "agent_token": None,
            "default_timeout_sec": 30,
            "max_message_bytes": 1024,
        }
        values.update(overrides)
        return self.service.ServiceConfig(**values)

    def decode_events(self, ws):
        return [json.loads(message) for message in ws.sent]

    def test_module_imports_without_websockets_installed(self):
        self.assertTrue(hasattr(self.service, "validate_request"))

    def test_load_json_message_validates_size_json_and_object(self):
        payload = self.service.load_json_message(b'{"task":"x"}', 20)
        self.assertEqual(payload, {"task": "x"})

        with self.assertRaisesRegex(ValueError, "too large"):
            self.service.load_json_message('{"task":"abcdef"}', 5)
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            self.service.load_json_message(b"\xff", 20)
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.service.load_json_message("{bad", 20)
        with self.assertRaisesRegex(ValueError, "JSON object"):
            self.service.load_json_message("[1, 2]", 20)

    def test_validate_request_normalizes_defaults(self):
        request = self.service.validate_request(
            {"task": "  Build analytics  ", "context": {"a": 1}, "params": {"b": 2}},
            default_timeout_sec=45,
        )

        self.assertEqual(request["type"], "analytics.request")
        self.assertEqual(request["task"], "Build analytics")
        self.assertEqual(request["context"], {"a": 1})
        self.assertEqual(request["params"], {"b": 2})
        self.assertEqual(request["timeout_sec"], 45)
        self.assertTrue(request["request_id"])
        self.assertIsInstance(request["created_ts_ms"], int)

    def test_validate_request_rejects_bad_shapes(self):
        cases = [
            ({}, "task"),
            ({"task": "x", "request_id": ""}, "request_id"),
            ({"task": "x", "timeout_sec": 0}, "timeout_sec"),
            ({"task": "x", "timeout_sec": True}, "timeout_sec"),
            ({"task": "x", "timeout_sec": 1.5}, "timeout_sec"),
            ({"task": "x", "context": []}, "context"),
            ({"task": "x", "params": []}, "params"),
        ]
        for payload, pattern in cases:
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(ValueError, pattern):
                    self.service.validate_request(payload, default_timeout_sec=30)

    def test_build_agent_payload_preserves_user_params_with_expected_mode(self):
        request = self.service.validate_request(
            {
                "request_id": "r1",
                "task": "Analyze",
                "context": {"portfolio": "P1"},
                "params": {"format": "brief", "mode": "custom"},
            },
            default_timeout_sec=30,
        )

        payload = self.service.build_agent_payload(request)

        self.assertEqual(payload["type"], "agent.task.request")
        self.assertEqual(payload["request_id"], "r1")
        self.assertEqual(payload["context"], {"portfolio": "P1"})
        self.assertEqual(payload["params"]["mode"], "custom")
        self.assertIn("expected_output", payload["params"])

    def test_normalize_agent_event_handles_json_text_and_binary(self):
        json_event = self.service.normalize_agent_event("r1", '{"type":"progress","value":10}')
        self.assertEqual(json_event["agent_event_type"], "progress")
        self.assertEqual(json_event["data"]["request_id"], "r1")

        text_event = self.service.normalize_agent_event("r1", "plain text")
        self.assertEqual(text_event["agent_event_type"], "text")
        self.assertEqual(text_event["data"], {"text": "plain text"})

        binary_event = self.service.normalize_agent_event("r1", b"\xff")
        self.assertEqual(binary_event["agent_event_type"], "binary")
        self.assertEqual(binary_event["data"], {"bytes": 1})

    def test_agent_event_is_terminal(self):
        self.assertEqual(
            self.service.agent_event_is_terminal({"data": {"type": "completed"}}),
            (True, False),
        )
        self.assertEqual(
            self.service.agent_event_is_terminal({"data": {"status": "failed"}}),
            (True, True),
        )
        self.assertEqual(self.service.agent_event_is_terminal({"data": {"type": "progress"}}), (False, False))

    def test_token_from_headers_supports_authorization_and_custom_header(self):
        self.assertEqual(
            self.service.token_from_headers(SimpleNamespace(request_headers={"Authorization": "Bearer abc"})),
            "abc",
        )
        self.assertEqual(
            self.service.token_from_headers(SimpleNamespace(request_headers={"X-WS-Token": "xyz"})),
            "xyz",
        )
        self.assertIsNone(self.service.token_from_headers(SimpleNamespace(request_headers={})))

    def test_handle_client_rejects_bad_inbound_token(self):
        ws = FakeWebSocket(headers={"Authorization": "Bearer wrong"})
        config = self.make_config(inbound_token="expected")

        asyncio.run(self.service.handle_client(ws, config))

        self.assertEqual(ws.closed, (4401, "unauthorized"))
        self.assertEqual(ws.sent, [])

    def test_handle_client_bad_request_stays_on_connection(self):
        ws = FakeWebSocket(messages=['{"context": {}}'])
        config = self.make_config()

        asyncio.run(self.service.handle_client(ws, config))

        events = self.decode_events(ws)
        self.assertEqual(events[0]["type"], "analytics.failed")
        self.assertEqual(events[0]["reason"], "bad_request")

    def test_handle_client_invalid_utf8_is_bad_request(self):
        ws = FakeWebSocket(messages=[b"\xff"])
        config = self.make_config()

        asyncio.run(self.service.handle_client(ws, config))

        events = self.decode_events(ws)
        self.assertEqual(events[0]["type"], "analytics.failed")
        self.assertEqual(events[0]["reason"], "bad_request")
        self.assertIn("UTF-8", events[0]["detail"])

    def test_main_missing_websockets_returns_clean_error(self):
        args = SimpleNamespace(
            demo_client=False,
            listen_host="127.0.0.1",
            listen_port=8787,
            agent_url="ws://agent.local/ws",
            inbound_token=None,
            agent_token=None,
            timeout_sec=30,
            max_message_bytes=1024,
            log_level="CRITICAL",
        )

        with patch.object(self.service, "parse_args", return_value=args):
            with patch.object(self.service, "run_server", side_effect=RuntimeError("Missing dependency: websockets")):
                with patch("sys.stderr", new=io.StringIO()):
                    result = self.service.main()

        self.assertEqual(result, 2)

    def test_delegate_to_agent_success_flow(self):
        client = FakeWebSocket()
        config = self.make_config(agent_token="secret")
        request = self.service.validate_request(
            {"request_id": "r1", "task": "Analyze", "timeout_sec": 5},
            default_timeout_sec=30,
        )
        agent = FakeAgentConnection([
            json.dumps({"type": "progress", "pct": 50}),
            json.dumps({"type": "completed", "result": {"ok": True}}),
        ])

        async def fake_connect(url, headers):
            self.assertEqual(url, config.agent_url)
            self.assertEqual(headers, {"Authorization": "Bearer secret"})
            return agent

        with patch.object(self.service, "connect_agent", side_effect=fake_connect):
            asyncio.run(self.service.delegate_to_agent(client, request, config))

        events = self.decode_events(client)
        self.assertEqual([event["type"] for event in events], [
            "analytics.accepted",
            "analytics.sent_to_agent",
            "analytics.agent_event",
            "analytics.agent_event",
            "analytics.completed",
        ])
        sent_payload = json.loads(agent.sent[0])
        self.assertEqual(sent_payload["request_id"], "r1")

    def test_delegate_to_agent_timeout_flow(self):
        client = FakeWebSocket()
        config = self.make_config()
        request = self.service.validate_request(
            {"request_id": "r1", "task": "Analyze", "timeout_sec": 1},
            default_timeout_sec=30,
        )
        agent = FakeAgentConnection([])

        async def fake_connect(url, headers):
            return agent

        with patch.object(self.service, "connect_agent", side_effect=fake_connect):
            asyncio.run(self.service.delegate_to_agent(client, request, config))

        events = self.decode_events(client)
        self.assertEqual(events[-1]["type"], "analytics.failed")
        self.assertEqual(events[-1]["reason"], "timeout")


if __name__ == "__main__":
    unittest.main()
