# encoding:utf-8

import sys
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

# Stub the config and common modules before importing the model
# so we don't need a real config.json
sys.modules.setdefault("config", MagicMock())
sys.modules.setdefault("common", MagicMock())
sys.modules.setdefault("common.const", MagicMock())
sys.modules.setdefault("common.log", MagicMock())

import config as config_mod
import common.const as const_mod

const_mod.LITELLM = "litellm"

# Default conf values returned by model_conf(const.LITELLM)
_DEFAULT_CONF = {
    "model": "openai/gpt-4o-mini",
    "api_key": "test-key-123",
    "api_base": "http://localhost:4000",
    "character_desc": "You are a helpful assistant",
    "temperature": 0.75,
    "max_tokens": 1000,
    "conversation_max_tokens": 1000,
    "max_history_num": 10,
}


def _model_conf_side_effect(model_type):
    if model_type == "litellm":
        return dict(_DEFAULT_CONF)
    return {}


def _common_conf_val_side_effect(key, default=None):
    defaults = {
        "clear_memory_commands": ["#clear memory"],
    }
    return defaults.get(key, default)


config_mod.model_conf = MagicMock(side_effect=_model_conf_side_effect)
config_mod.common_conf_val = MagicMock(side_effect=_common_conf_val_side_effect)

# Now import the module under test
from model.litellm.litellm_model import LiteLLMModel, Session, user_session

# Import real litellm exceptions for raising in mocks
from litellm.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    Timeout,
    NotFoundError,
    BadRequestError,
    ContextWindowExceededError,
)


def _make_mock_response(content="Hello!", total_tokens=42):
    """Build a mock litellm.completion response."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    usage = MagicMock()
    usage.total_tokens = total_tokens
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def _litellm_exception(exc_class, message="test error"):
    """Instantiate a litellm exception the way litellm does it internally."""
    return exc_class(
        message=message,
        model="openai/gpt-4o-mini",
        llm_provider="openai",
    )


class TestLiteLLMModelInit(unittest.TestCase):
    """Test LiteLLMModel initialisation and default config."""

    def test_default_model_format(self):
        """Default model must be provider-prefixed: openai/gpt-4o-mini."""
        model = LiteLLMModel()
        self.assertEqual(model.model, "openai/gpt-4o-mini")

    def test_custom_model_from_conf(self):
        custom = dict(_DEFAULT_CONF, model="anthropic/claude-sonnet-4-20250514")
        with patch("model.litellm.litellm_model.model_conf", return_value=custom):
            m = LiteLLMModel()
            self.assertEqual(m.model, "anthropic/claude-sonnet-4-20250514")

    def test_api_key_loaded(self):
        model = LiteLLMModel()
        self.assertEqual(model.api_key, "test-key-123")

    def test_api_base_loaded(self):
        model = LiteLLMModel()
        self.assertEqual(model.api_base, "http://localhost:4000")


class TestBuildCallKwargs(unittest.TestCase):
    """Test _build_call_kwargs helper."""

    def setUp(self):
        self.model = LiteLLMModel()

    def test_drop_params_is_true(self):
        """drop_params=True must always be passed so unsupported params are silently dropped."""
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertTrue(kwargs["drop_params"])

    def test_stream_flag_default_false(self):
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertFalse(kwargs["stream"])

    def test_stream_flag_true(self):
        kwargs = self.model._build_call_kwargs(
            [{"role": "user", "content": "hi"}], stream=True
        )
        self.assertTrue(kwargs["stream"])

    def test_api_key_included(self):
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertEqual(kwargs["api_key"], "test-key-123")

    def test_api_base_included(self):
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertEqual(kwargs["api_base"], "http://localhost:4000")

    def test_model_name_in_kwargs(self):
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertEqual(kwargs["model"], "openai/gpt-4o-mini")

    def test_no_api_key_when_empty(self):
        self.model.api_key = ""
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertNotIn("api_key", kwargs)

    def test_no_api_base_when_empty(self):
        self.model.api_base = ""
        kwargs = self.model._build_call_kwargs([{"role": "user", "content": "hi"}])
        self.assertNotIn("api_base", kwargs)


class TestReplyTextHappyPath(unittest.TestCase):
    """Test reply_text returns content on successful completion."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_happy_path_returns_content(self, mock_litellm):
        mock_litellm.completion.return_value = _make_mock_response("Hi there!")
        messages = [{"role": "user", "content": "hello"}]
        result = self.model.reply_text(messages, "user1")
        self.assertEqual(result, "Hi there!")
        mock_litellm.completion.assert_called_once()

    @patch("model.litellm.litellm_model.litellm")
    def test_strips_whitespace(self, mock_litellm):
        mock_litellm.completion.return_value = _make_mock_response("  spaced  ")
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertEqual(result, "spaced")


class TestReplyTextEmptyResponse(unittest.TestCase):
    """Test reply_text handles empty/null content without crashing."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_none_content_returns_empty_string(self, mock_litellm):
        mock_litellm.completion.return_value = _make_mock_response(content=None)
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertEqual(result, "")

    @patch("model.litellm.litellm_model.litellm")
    def test_empty_string_content(self, mock_litellm):
        mock_litellm.completion.return_value = _make_mock_response(content="")
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertEqual(result, "")


class TestReplyTextAuthenticationError(unittest.TestCase):
    """Test reply_text handles AuthenticationError."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_auth_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            AuthenticationError, "Invalid API key"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Authentication failed", result)
        self.assertIn("API key", result)


class TestReplyTextNotFoundError(unittest.TestCase):
    """Test reply_text handles NotFoundError (model not found)."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_not_found_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            NotFoundError, "Model does not exist"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Model not found", result)


class TestReplyTextRateLimitRetry(unittest.TestCase):
    """Test reply_text retries on RateLimitError then gives up after 3 retries."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.time.sleep")
    @patch("model.litellm.litellm_model.litellm")
    def test_rate_limit_retries_then_succeeds(self, mock_litellm, mock_sleep):
        """First call raises RateLimitError, second succeeds."""
        mock_litellm.completion.side_effect = [
            _litellm_exception(RateLimitError, "rate limited"),
            _make_mock_response("recovered"),
        ]
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertEqual(result, "recovered")
        self.assertEqual(mock_litellm.completion.call_count, 2)
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1

    @patch("model.litellm.litellm_model.time.sleep")
    @patch("model.litellm.litellm_model.litellm")
    def test_rate_limit_exhausts_retries(self, mock_litellm, mock_sleep):
        """All 4 attempts (0,1,2,3) raise RateLimitError -> gives up."""
        mock_litellm.completion.side_effect = _litellm_exception(
            RateLimitError, "rate limited"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Rate limit exceeded", result)
        self.assertEqual(mock_litellm.completion.call_count, 4)
        # sleep was called with 1, 2, 4 (exponential backoff)
        sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
        self.assertEqual(sleep_args, [1, 2, 4])


class TestReplyTextContextWindowExceeded(unittest.TestCase):
    """Test reply_text handles ContextWindowExceededError."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_context_window_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            ContextWindowExceededError, "too many tokens"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Context window exceeded", result)
        # Session should be cleared
        self.assertEqual(user_session.get("user1", []), [])


class TestReplyTextTimeout(unittest.TestCase):
    """Test reply_text handles Timeout exception."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_timeout_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            Timeout, "request timed out"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Connection error", result)


class TestReplyTextAPIConnectionError(unittest.TestCase):
    """Test reply_text handles APIConnectionError."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_connection_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            APIConnectionError, "connection refused"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Connection error", result)


class TestReplyTextBadRequest(unittest.TestCase):
    """Test reply_text handles BadRequestError."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_bad_request_error_message(self, mock_litellm):
        mock_litellm.completion.side_effect = _litellm_exception(
            BadRequestError, "invalid input"
        )
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("Bad request", result)


class TestReplyTextGenericException(unittest.TestCase):
    """Test reply_text handles unexpected exceptions gracefully."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_generic_exception_clears_session(self, mock_litellm):
        mock_litellm.completion.side_effect = RuntimeError("something unexpected")
        result = self.model.reply_text(
            [{"role": "user", "content": "q"}], "user1"
        )
        self.assertIn("error occurred", result)
        self.assertEqual(user_session.get("user1", []), [])


class TestReplyDispatch(unittest.TestCase):
    """Test the top-level reply() method dispatches correctly."""

    def setUp(self):
        user_session.clear()
        self.model = LiteLLMModel()

    @patch("model.litellm.litellm_model.litellm")
    def test_reply_text_type(self, mock_litellm):
        mock_litellm.completion.return_value = _make_mock_response("answer")
        context = {
            "type": "TEXT",
            "from_user_id": "user1",
        }
        result = self.model.reply("hello", context)
        self.assertEqual(result, "answer")

    @patch("model.litellm.litellm_model.litellm")
    def test_reply_clear_memory(self, mock_litellm):
        context = {
            "type": "TEXT",
            "from_user_id": "user1",
        }
        result = self.model.reply("#clear memory", context)
        self.assertEqual(result, "Memory cleared")

    def test_reply_non_text_returns_none(self):
        context = {
            "type": "IMAGE",
            "from_user_id": "user1",
        }
        result = self.model.reply("hello", context)
        self.assertIsNone(result)


class TestSession(unittest.TestCase):
    """Test Session helper methods."""

    def setUp(self):
        user_session.clear()

    def test_build_session_query_adds_system_prompt(self):
        messages = Session.build_session_query("hi", "user1")
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertEqual(messages[-1]["content"], "hi")

    def test_build_session_query_appends_to_existing(self):
        Session.build_session_query("first", "user1")
        messages = Session.build_session_query("second", "user1")
        user_messages = [m for m in messages if m["role"] == "user"]
        self.assertEqual(len(user_messages), 2)

    def test_clear_session(self):
        Session.build_session_query("hi", "user1")
        Session.clear_session("user1")
        self.assertEqual(user_session["user1"], [])

    def test_save_session_appends_assistant(self):
        Session.build_session_query("hi", "user1")
        Session.save_session("hi", "response", "user1", used_tokens=10)
        session = user_session["user1"]
        self.assertEqual(session[-1]["role"], "assistant")
        self.assertEqual(session[-1]["content"], "response")

    def test_save_session_trims_when_over_token_limit(self):
        Session.build_session_query("q1", "user1")
        Session.save_session("q1", "a1", "user1", used_tokens=10)
        Session.build_session_query("q2", "user1")
        # Trigger trim by exceeding max_tokens (1000)
        Session.save_session("q2", "a2", "user1", used_tokens=2000)
        session = user_session["user1"]
        # system prompt should remain, but oldest Q/A pair trimmed
        self.assertEqual(session[0]["role"], "system")
        # At least one pair was removed
        user_msgs = [m for m in session if m["role"] == "user"]
        self.assertTrue(len(user_msgs) <= 2)


if __name__ == "__main__":
    unittest.main()
