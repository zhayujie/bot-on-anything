"""Exercise discovered plugin/Bridge callers with real Requests redirect handling."""

import asyncio
import copy
import io
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests
from requests.adapters import HTTPAdapter

import config
from bridge.bridge import Bridge
from plugins.plugin_manager import PluginManager


ENDPOINT = "https://search.parallel.ai/mcp"
UNAVAILABLE = "Parallel Search is unavailable. Please try again later."
METHODS = ("initialize", "notifications/initialized", "tools/call")
DESTINATIONS = ("https://search.parallel.ai/redirected",
                "https://destination.invalid/redirected",
                "http://search.parallel.ai/redirected")


class FixtureAdapter(HTTPAdapter):
    """Only the transport is synthetic; Session.send and its hooks are real."""

    def __init__(self, test):
        super().__init__()
        self.test = test
        self.closed = False

    def send(self, request, **kwargs):
        return self.test.send(request, **kwargs)

    def close(self):
        self.closed = True
        super().close()


class FixtureBody(io.BytesIO):
    def __init__(self, body):
        super().__init__(body)
        self.released = False

    def release_conn(self):
        self.released = True


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
        self.addCleanup(setattr, config, "config", self.saved_config)
        self.context = {"from_user_id": "fixture-user", "model": "linkai"}
        self.requests = []
        self.responses = []
        self.sessions = []
        self.adapters = []
        self.resolve_statuses = []
        self.mode = "json"
        self.redirect = None
        self.bypass_hook = False
        self.follow_redirects = False
        self.results = [{"title": "Python asyncio", "url": "https://docs.python.org/3/library/asyncio.html",
                         "excerpts": ["asyncio is a library to write concurrent code."]}]
        # All netrc reads, including negative controls, are disposable and fake-only.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.netrc = os.path.join(directory.name, "netrc")
        with open(self.netrc, "w") as file:
            file.write("machine search.parallel.ai login fixture-user password fixture-password\n"
                       "default login fixture-default password fixture-default-password\n")
        os.chmod(self.netrc, 0o600)
        self.start_patch(patch.dict(os.environ, {"NETRC": self.netrc,
                         "PARALLEL_API_KEY": "fixture-unused", "OPENAI_API_KEY": "fixture-unused"}, clear=True))
        real_session = requests.sessions.Session
        real_resolve = real_session.resolve_redirects

        def resolve(session, response, request, **kwargs):
            self.resolve_statuses.append(response.status_code)
            return real_resolve(session, response, request, **kwargs)

        self.start_patch(patch.object(real_session, "resolve_redirects", resolve))
        self.netrc_lookup = self.start_patch(patch("requests.sessions.get_netrc_auth",
                                                  wraps=requests.sessions.get_netrc_auth))
        self.rebuild_auth = self.start_patch(patch.object(real_session, "rebuild_auth", autospec=True,
                                                         side_effect=real_session.rebuild_auth))

        def session_factory():
            session = real_session()
            self.sessions.append(session)
            adapter = FixtureAdapter(self)
            self.adapters.append(adapter)
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            post = session.post

            def observed_post(*args, **kwargs):
                self.assertIs(kwargs.get("allow_redirects"), False)
                if self.bypass_hook:
                    # Negative controls recreate the old flaw without replacing send.
                    session.hooks["response"] = []
                    kwargs["allow_redirects"] = self.follow_redirects
                return post(*args, **kwargs)

            session.post = observed_post
            return session

        self.start_patch(patch("requests.Session", side_effect=session_factory))
        self.factory = self.start_patch(patch("bridge.bridge.model_factory.create_bot"))

    def start_patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def response(self, request, status, data, event_stream=False):
        response = requests.Response()
        response.status_code = status
        response.request = request
        response.url = request.url
        response.encoding = "utf-8"
        response.headers["Content-Type"] = "text/event-stream" if event_stream else "application/json"
        body = json.dumps(data)
        if event_stream:
            body = ': keepalive\n\nevent: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n' + "data: " + body + "\n\n"
        response.raw = FixtureBody(body.encode())
        response.close = Mock(wraps=response.close)
        self.responses.append(response)
        return response

    def send(self, request, **kwargs):
        self.requests.append((request, kwargs))
        if request.url != ENDPOINT:
            # Reachable only in negative controls: record destination auth verbatim.
            return self.response(request, 200, {"id": 1, "result": {"protocolVersion": "2025-03-26"}})
        self.assertEqual(request.headers["User-Agent"], "bot-on-anything/parallel-search")
        self.assertEqual(request.headers["Accept"], "application/json, text/event-stream")
        self.assertNotIn("Authorization", request.headers)
        self.assertNotIn("Proxy-Authorization", request.headers)
        self.assertEqual(kwargs["timeout"], (5, 30))
        self.assertTrue(kwargs["stream"])
        payload = json.loads(request.body)
        method = payload["method"]
        if self.redirect is not None and method == self.redirect[0]:
            response = self.response(request, self.redirect[1], {})
            if self.redirect[2] is not None:
                response.headers["Location"] = self.redirect[2]
            return response
        if method == "initialize":
            self.assertEqual(payload["params"]["clientInfo"]["name"], "bot-on-anything")
            response = self.response(request, 200, {"id": 1, "result": {"protocolVersion": "2025-03-26"}}, self.mode == "sse")
            response.headers["Mcp-Session-Id"] = "fixture-mcp-session"
            return response
        self.assertEqual(request.headers["Mcp-Session-Id"], "fixture-mcp-session")
        self.assertEqual(request.headers["MCP-Protocol-Version"], "2025-03-26")
        if method == "notifications/initialized":
            return self.response(request, 202, None)
        self.assertEqual(method, "tools/call")
        self.assertEqual(payload["params"]["name"], "web_search")
        self.assertEqual(payload["params"]["arguments"], {
            "objective": "Python asyncio documentation", "search_queries": ["Python asyncio documentation"]})
        if self.mode == "timeout":
            raise requests.ReadTimeout()
        if self.mode == "cancel":
            raise KeyboardInterrupt()
        if self.mode == "async_cancel":
            raise asyncio.CancelledError()
        if self.mode == "http_error":
            return self.response(request, 429, {"error": "fixture quota"})
        if self.mode == "rpc_error":
            return self.response(request, 200, {"id": 2, "error": {"code": -32603, "message": "fixture failure"}})
        if self.mode == "tool_error":
            return self.response(request, 200, {"id": 2, "result": {"isError": True, "content": []}})
        if self.mode == "malformed":
            return self.response(request, 200, {"id": 2, "result": {"structuredContent": {"results": None}}})
        result = {"results": self.results}
        if self.mode == "text":
            result = {"content": [{"type": "text", "text": json.dumps(result)}]}
        else:
            result = {"structuredContent": result}
        return self.response(request, 200, {"id": 2, "result": result}, self.mode == "sse")

    def call(self, streaming=False, query="/search Python asyncio documentation", context=None):
        context = self.context if context is None else context
        if not streaming:
            return Bridge().fetch_reply_content(query, context)

        async def collect():
            return [item async for item in Bridge().fetch_reply_stream(query, context)]
        packets = asyncio.run(collect())
        self.assertEqual(len(packets), 1)
        self.assertTrue(packets[0][0])
        return packets[0][1]

    def assert_closed(self):
        self.assertTrue(all(response.close.called for response in self.responses))
        self.assertTrue(all(response.raw.closed or response.raw.released for response in self.responses))
        self.assertTrue(all(adapter.closed for adapter in self.adapters))

    def test_loaded_plugin_returns_sources_for_json_text_and_sse(self):
        for streaming in (False, True):
            for mode in ("json", "text", "sse"):
                with self.subTest(streaming=streaming, mode=mode):
                    self.mode = mode
                    reply = self.call(streaming)
                    self.assertIn("Python asyncio", reply)
                    self.assertIn(self.results[0]["url"], reply)
                    self.assertIn(self.results[0]["excerpts"][0], reply)
        self.assertEqual(len(self.requests), 18)
        self.assert_closed()
        self.assertEqual(self.context, {"from_user_id": "fixture-user", "model": "linkai"})
        self.netrc_lookup.assert_not_called()
        self.factory.assert_not_called()

    def test_all_3xx_rejected_before_redirect_preparation_at_every_rpc_stage(self):
        for streaming in (False, True):
            for status in range(300, 400):
                for index, method in enumerate(METHODS):
                    for destination in DESTINATIONS + (None,):
                        with self.subTest(streaming=streaming, status=status, method=method, destination=destination):
                            self.requests.clear()
                            self.responses.clear()
                            self.resolve_statuses.clear()
                            self.redirect = (method, status, destination)
                            self.assertEqual(self.call(streaming), UNAVAILABLE)
                            self.assertEqual(len(self.requests), index + 1)
                            self.assertEqual([json.loads(r.body)["method"] for r, _ in self.requests],
                                             list(METHODS[:index + 1]))
                            self.assertTrue(all(r.url == ENDPOINT for r, _ in self.requests))
                            self.assertEqual(self.resolve_statuses, [200, 202][:index])
                            self.assertIsNone(self.responses[-1].next)
                            self.assertTrue(self.responses[-1].raw.closed)
                            self.netrc_lookup.assert_not_called()
                            self.rebuild_auth.assert_not_called()
                            self.assert_closed()
        self.factory.assert_not_called()

    def test_negative_controls_detect_old_redirect_auth_and_response_next(self):
        self.bypass_hook = True
        for follow in (False, True):
            self.follow_redirects = follow
            for status in (301, 302, 303, 307, 308):
                for destination in DESTINATIONS:
                    with self.subTest(follow=follow, status=status, destination=destination):
                        self.requests.clear()
                        self.responses.clear()
                        self.netrc_lookup.reset_mock()
                        self.rebuild_auth.reset_mock()
                        self.redirect = ("initialize", status, destination)
                        self.call()
                        self.netrc_lookup.assert_called()
                        self.rebuild_auth.assert_called()
                        self.assertEqual(self.netrc_lookup.call_args.args[0], destination)
                        if follow:
                            destinations = [r for r, _ in self.requests if r.url != ENDPOINT]
                            self.assertEqual(len(destinations), 1)
                            self.assertIn("Authorization", destinations[0].headers)
                        else:
                            self.assertEqual(len(self.requests), 1)
                            self.assertIsNotNone(self.responses[0].next)
                            self.assertIn("Authorization", self.responses[0].next.headers)
                        self.assert_closed()
        self.factory.assert_not_called()

    def test_optional_session_argument_absent_across_distinct_callers_and_errors(self):
        contexts = ({"from_user_id": "telegram-chat-a", "model": "linkai"},
                    {"from_user_id": "telegram-chat-b", "model": "linkai"},
                    {"session_id": "http-user-a", "model": "linkai"},
                    {"session_id": "http-user-b", "model": "linkai"})
        self.assertIs(self.manager, PluginManager())
        self.assertIs(self.plugin, PluginManager().plugin_registry.get_plugin("ParallelSearch"))
        self.assertFalse(hasattr(self.plugin, "session_id"))
        for context in contexts:
            saved = copy.deepcopy(context)
            for mode in ("json", "timeout", "json", "http_error", "text"):
                for streaming in (False, True):
                    self.mode = mode
                    reply = self.call(streaming, context=context)
                    self.assertEqual(reply == UNAVAILABLE, mode in ("timeout", "http_error"))
                    self.assertEqual(context, saved)
        calls = [json.loads(r.body)["params"]["arguments"] for r, _ in self.requests
                 if json.loads(r.body)["method"] == "tools/call"]
        self.assertEqual(len(calls), 40)
        self.assertTrue(all(set(arguments) == {"objective", "search_queries"} for arguments in calls))
        self.netrc_lookup.assert_not_called()
        self.assert_closed()
        self.factory.assert_not_called()

    def test_proxy_and_ca_environment_settings_reach_adapter(self):
        for ca_variable in ("REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
            with self.subTest(ca_variable=ca_variable):
                self.requests.clear()
                with patch.dict(os.environ, {"HTTPS_PROXY": "http://proxy.invalid:8080",
                                             ca_variable: "/fixture/ca-bundle.pem"}):
                    self.assertIn("Python asyncio", self.call())
                for request, kwargs in self.requests:
                    self.assertEqual(kwargs["proxies"]["https"], "http://proxy.invalid:8080")
                    self.assertEqual(kwargs["verify"], "/fixture/ca-bundle.pem")
        self.netrc_lookup.assert_not_called()
        self.factory.assert_not_called()

    def test_disabled_missing_and_non_boolean_settings_preserve_selected_model(self):
        self.factory.return_value.reply.return_value = "selected model reply"

        async def model_stream(query, context):
            yield True, "selected model reply"
        self.factory.return_value.reply_text_stream = model_stream
        for common in ({}, {"parallel_search_enabled": False}, {"parallel_search_enabled": "false"},
                       {"parallel_search_enabled": "true"}, {"parallel_search_enabled": 1},
                       {"parallel_search_enabled": None}):
            config.config["common"] = common
            for streaming in (False, True):
                self.assertEqual(self.call(streaming), "selected model reply")
        self.assertEqual(self.requests, [])
        self.factory.assert_called_with("linkai")

    def test_ordinary_messages_and_other_commands_preserve_selection(self):
        self.factory.return_value.reply.return_value = "normal reply"

        async def model_stream(query, context):
            yield True, "normal reply"
        self.factory.return_value.reply_text_stream = model_stream
        for query in ("hello", "/searching asyncio", "#清除记忆"):
            for streaming in (False, True):
                self.assertEqual(self.call(streaming, query=query), "normal reply")
            self.factory.return_value.reply.assert_called_with(query, self.context)
        self.factory.assert_called_with("linkai")
        self.assertEqual(self.requests, [])

    def test_image_requests_keep_their_original_model_path(self):
        self.context["type"] = "IMAGE_CREATE"
        self.factory.return_value.reply.return_value = ["https://example.com/image.png"]
        self.assertEqual(self.call(), ["https://example.com/image.png"])
        self.factory.return_value.reply.assert_called_once_with(
            "/search Python asyncio documentation", self.context)
        self.factory.assert_called_once_with("linkai")
        self.assertEqual(self.requests, [])

    def test_usage_and_empty_results(self):
        for streaming in (False, True):
            self.assertEqual(self.call(streaming, query="/search  "), "Usage: /search <query>")
        self.assertEqual(self.requests, [])
        self.results = []
        for streaming in (False, True):
            self.assertEqual(self.call(streaming), "No web results found.")
        self.factory.assert_not_called()

    def test_errors_do_not_retry_or_fall_back_to_model(self):
        for streaming in (False, True):
            for mode in ("timeout", "http_error", "rpc_error", "tool_error", "malformed"):
                with self.subTest(streaming=streaming, mode=mode):
                    self.mode = mode
                    self.requests.clear()
                    self.assertEqual(self.call(streaming), UNAVAILABLE)
                    self.assertEqual(len(self.requests), 3)
        self.assert_closed()
        self.factory.assert_not_called()

    def test_cancellation_propagates_without_retry_or_model_call(self):
        for streaming in (False, True):
            for mode, exception in (("cancel", KeyboardInterrupt), ("async_cancel", asyncio.CancelledError)):
                with self.subTest(streaming=streaming, mode=mode):
                    self.mode = mode
                    self.requests.clear()
                    with self.assertRaises(exception):
                        self.call(streaming)
                    self.assertEqual(len(self.requests), 3)
        self.assert_closed()
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
