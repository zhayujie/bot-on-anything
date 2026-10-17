"""Exercise the loaded plugin through the same bridge used by channels."""

import asyncio
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import config
from bridge.bridge import Bridge
from plugins.plugin_manager import PluginManager


class ParallelSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = PluginManager()
        cls.plugin = cls.manager.plugin_registry.get_plugin("ParallelSearch")
        if cls.plugin is None:
            raise AssertionError("ParallelSearch was not discovered by PluginManager")

    def setUp(self):
        self.saved_config = copy.deepcopy(config.config)
        config.config = {"model": {"type": "chatgpt"}, "common": {"parallel_search_enabled": True}}
        self.context = {"from_user_id": "fixture-user", "model": "linkai"}
        self.requests = []
        self.responses = []
        self.mode = "json"
        self.results = [{"title": "Python asyncio", "url": "https://docs.python.org/3/library/asyncio.html",
                         "excerpts": ["asyncio is a library to write concurrent code."]}]
        self.send_patch = patch("requests.sessions.Session.send", side_effect=self.send)
        self.send_patch.start()
        self.factory_patch = patch("bridge.bridge.model_factory.create_bot")
        self.factory = self.factory_patch.start()
        self.addCleanup(self.send_patch.stop)
        self.addCleanup(self.factory_patch.stop)
        self.addCleanup(setattr, config, "config", self.saved_config)

    def response(self, status, data, event_stream=False):
        response = requests.Response()
        response.status_code = status
        response.encoding = "utf-8"
        response.headers["Content-Type"] = "text/event-stream" if event_stream else "application/json"
        body = json.dumps(data)
        if event_stream:
            body = ': keepalive\n\nevent: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n' + "data: " + body + "\n\n"
        response._content = body.encode()
        response._content_consumed = True
        response.close = Mock(wraps=response.close)
        self.responses.append(response)
        return response

    def send(self, request, **kwargs):
        # Observe real PreparedRequests, including authentication and transport options.
        self.assertEqual(request.url, "https://search.parallel.ai/mcp")
        self.assertEqual(request.headers["User-Agent"], "bot-on-anything/parallel-search")
        self.assertEqual(request.headers["Accept"], "application/json, text/event-stream")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(kwargs["timeout"], (5, 30))
        self.assertTrue(kwargs["stream"])
        payload = json.loads(request.body)
        self.requests.append(payload)
        method = payload["method"]
        if method == "initialize":
            self.assertEqual(payload["params"]["clientInfo"]["name"], "bot-on-anything")
            response = self.response(200, {"id": 1, "result": {"protocolVersion": "2025-03-26"}}, self.mode == "sse")
            response.headers["Mcp-Session-Id"] = "fixture-mcp-session"
            return response
        self.assertEqual(request.headers["Mcp-Session-Id"], "fixture-mcp-session")
        self.assertEqual(request.headers["MCP-Protocol-Version"], "2025-03-26")
        if method == "notifications/initialized":
            return self.response(202, None)
        self.assertEqual(method, "tools/call")
        self.assertEqual(payload["params"]["name"], "web_search")
        arguments = payload["params"]["arguments"]
        self.assertEqual(arguments["objective"], "Python asyncio documentation")
        self.assertEqual(arguments["search_queries"], ["Python asyncio documentation"])
        self.assertEqual(arguments["session_id"], self.plugin.session_id)
        self.assertNotIn("model_name", arguments)
        if self.mode == "timeout":
            raise requests.ReadTimeout()
        if self.mode == "cancel":
            raise KeyboardInterrupt()
        if self.mode == "http_error":
            return self.response(429, {"error": "quota"})
        if self.mode == "rpc_error":
            return self.response(200, {"id": 2, "error": {"code": -32603, "message": "failed"}})
        if self.mode == "tool_error":
            return self.response(200, {"id": 2, "result": {"isError": True, "content": []}})
        if self.mode == "malformed":
            return self.response(200, {"id": 2, "result": {"structuredContent": {"results": None}}})
        result = {"results": self.results}
        if self.mode == "text":
            result = {"content": [{"type": "text", "text": json.dumps(result)}]}
        else:
            result = {"structuredContent": result}
        return self.response(200, {"id": 2, "result": result}, self.mode == "sse")

    def call(self):
        return Bridge().fetch_reply_content("/search Python asyncio documentation", self.context)

    def test_loaded_plugin_returns_sources_for_json_text_and_sse(self):
        for mode in ("json", "text", "sse"):
            with self.subTest(mode=mode):
                self.mode = mode
                reply = self.call()
                self.assertIn("Python asyncio", reply)
                self.assertIn(self.results[0]["url"], reply)
                self.assertIn(self.results[0]["excerpts"][0], reply)
        self.assertEqual(len(self.requests), 9)
        self.assertTrue(all(r.close.called for r in self.responses))
        self.assertEqual(self.context, {"from_user_id": "fixture-user", "model": "linkai"})
        self.factory.assert_not_called()

    def test_anonymous_even_with_saved_credentials_and_environment_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            netrc = os.path.join(directory, "netrc")
            with open(netrc, "w") as file:
                file.write("machine search.parallel.ai login saved password secret\n")
            with patch.dict(os.environ, {"NETRC": netrc, "PARALLEL_API_KEY": "unused", "OPENAI_API_KEY": "unused"}):
                self.assertIn("Python asyncio", self.call())
        self.factory.assert_not_called()

    def test_disabled_missing_and_non_boolean_settings_preserve_selected_model(self):
        self.factory.return_value.reply.return_value = "selected model reply"
        for common in ({}, {"parallel_search_enabled": False}, {"parallel_search_enabled": "false"}):
            config.config["common"] = common
            self.assertEqual(self.call(), "selected model reply")
        self.assertEqual(self.requests, [])
        self.factory.assert_called_with("linkai")

    def test_ordinary_messages_and_other_commands_preserve_selection(self):
        self.factory.return_value.reply.return_value = "normal reply"
        for query in ("hello", "/searching asyncio", "#清除记忆"):
            self.assertEqual(Bridge().fetch_reply_content(query, self.context), "normal reply")
            self.factory.return_value.reply.assert_called_with(query, self.context)
        self.factory.assert_called_with("linkai")
        self.assertEqual(self.requests, [])

    def test_image_requests_keep_their_original_model_path(self):
        self.context["type"] = "IMAGE_CREATE"
        self.factory.return_value.reply.return_value = ["https://example.com/image.png"]
        self.assertEqual(self.call(), ["https://example.com/image.png"])
        self.factory.return_value.reply.assert_called_once_with(
            "/search Python asyncio documentation", self.context)
        self.assertEqual(self.requests, [])

    def test_usage_and_empty_results(self):
        self.assertEqual(Bridge().fetch_reply_content("/search  ", self.context), "Usage: /search <query>")
        self.assertEqual(self.requests, [])
        self.results = []
        self.assertEqual(self.call(), "No web results found.")
        self.factory.assert_not_called()

    def test_errors_do_not_retry_or_fall_back_to_model(self):
        for mode in ("timeout", "http_error", "rpc_error", "tool_error", "malformed"):
            with self.subTest(mode=mode):
                self.mode = mode
                self.requests.clear()
                self.assertEqual(self.call(), "Parallel Search is unavailable. Please try again later.")
                self.assertEqual(len(self.requests), 3)
        self.assertTrue(all(r.close.called for r in self.responses))
        self.factory.assert_not_called()

    def test_cancellation_propagates_without_retry_or_model_call(self):
        self.mode = "cancel"
        with self.assertRaises(KeyboardInterrupt):
            self.call()
        self.assertEqual(len(self.requests), 3)
        self.assertTrue(all(r.close.called for r in self.responses))
        self.factory.assert_not_called()

    def test_streaming_intercept_does_not_construct_model(self):
        async def collect():
            return [item async for item in Bridge().fetch_reply_stream(
                "/search Python asyncio documentation", self.context)]
        packets = asyncio.run(collect())
        self.assertEqual(len(packets), 1)
        self.assertTrue(packets[0][0])
        self.assertIn(self.results[0]["url"], packets[0][1])
        self.factory.assert_not_called()

    def test_streaming_ordinary_message_uses_selected_model(self):
        async def model_stream(query, context):
            self.assertEqual(query, "hello")
            self.assertIs(context, self.context)
            yield False, "part"
            yield True, "whole"
        self.factory.return_value.reply_text_stream = model_stream

        async def collect():
            return [item async for item in Bridge().fetch_reply_stream("hello", self.context)]
        self.assertEqual(asyncio.run(collect()), [(False, "part"), (True, "whole")])
        self.factory.assert_called_once_with("linkai")
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
