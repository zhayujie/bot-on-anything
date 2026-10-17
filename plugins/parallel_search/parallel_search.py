"""An explicit, opt-in web search command using the anonymous Parallel MCP."""

import json
import uuid

import requests

import plugins
from config import common_conf_val
from plugins import Event, EventAction, Plugin


ENDPOINT = "https://search.parallel.ai/mcp"
USER_AGENT = "bot-on-anything/parallel-search"


def _rpc(session, method, params=None, request_id=None):
    payload = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        payload["params"] = params
    if request_id is not None:
        payload["id"] = request_id
    with session.post(ENDPOINT, json=payload, timeout=(5, 30), stream=True) as response:
        response.raise_for_status()
        if response.headers.get("Mcp-Session-Id"):
            session.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
        if request_id is None:
            return None
        if "text/event-stream" in response.headers.get("Content-Type", ""):
            response.encoding = "utf-8"
            data = []
            message = None
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data:"):
                    data.append(line[5:].lstrip(" "))
                elif not line and data:
                    candidate = json.loads("\n".join(data))
                    data = []
                    if candidate.get("id") == request_id:
                        message = candidate
                        break
        else:
            message = response.json()
        if not isinstance(message, dict) or message.get("id") != request_id or "error" in message:
            raise ValueError("Invalid MCP response")
        return message["result"]


def _search(query, session_id):
    with requests.Session() as session:
        # Keep proxy settings, but never load credentials from ~/.netrc.
        session.auth = lambda request: request
        session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/event-stream",
        })
        initialized = _rpc(session, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "bot-on-anything", "version": "1.0"},
        }, 1)
        protocol = initialized["protocolVersion"]
        if protocol not in ("2024-11-05", "2025-03-26"):
            raise ValueError("Unsupported MCP protocol version")
        session.headers["MCP-Protocol-Version"] = protocol
        _rpc(session, "notifications/initialized")
        result = _rpc(session, "tools/call", {
            "name": "web_search",
            "arguments": {"objective": query, "search_queries": [query], "session_id": session_id},
        }, 2)
        if result.get("isError"):
            raise ValueError("Search tool failed")
        content = result.get("structuredContent")
        if content is None:
            content = json.loads("\n".join(
                item["text"] for item in result["content"] if item.get("type") == "text"
            ))
        results = content["results"]
        if not isinstance(results, list):
            raise ValueError("Invalid search results")
        entries = []
        for index, item in enumerate(results[:3], 1):
            url = item["url"]
            if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                raise ValueError("Invalid result URL")
            title = (item.get("title") or url).replace("\n", " ")[:120]
            excerpt = " ".join(item.get("excerpts", []))[:400]
            entries.append("{}. {}\n{}\n{}".format(index, title, url, excerpt).rstrip())
        return "\n\n".join(entries) if entries else "No web results found."


@plugins.register(name="ParallelSearch", desire_priority=80,
                  desc="Opt-in /search command", version="0.1", author="Parallel")
class ParallelSearch(Plugin):
    def __init__(self):
        super().__init__()
        # Reuse one anonymous identifier for this plugin instance, including errors.
        self.session_id = str(uuid.uuid4())
        self.handlers[Event.ON_BRIDGE_HANDLE_CONTEXT] = self.search

    def get_help_text(self, **kwargs):
        return "/search <query>: search the web (requires common.parallel_search_enabled)."

    def search(self, e_context):
        if common_conf_val("parallel_search_enabled", False) is not True:
            return
        if (e_context["args"] or {}).get("type") not in (None, "", "TEXT"):
            return
        query = e_context["context"]
        if not isinstance(query, str):
            return
        parts = query.strip().split(None, 1)
        if not parts or parts[0] != "/search":
            return
        if len(parts) == 1:
            reply = "Usage: /search <query>"
        else:
            try:
                reply = _search(parts[1], self.session_id)
            except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
                reply = "Parallel Search is unavailable. Please try again later."
        e_context["reply"] = reply
        e_context.action = EventAction.BREAK_PASS
