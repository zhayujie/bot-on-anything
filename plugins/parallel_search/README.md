# Parallel Search

Use `/search <query>` to get current web results with source links and short
excerpts through [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp).
Search uses Fast mode and requires no Parallel account or API key. The anonymous
service is intended for light use and has rate limits.

The plugin is disabled by default. To enable it, add this setting to the existing
`common` object in your `config.json`, keeping your other settings:

```json
"parallel_search_enabled": true
```

It uses `requests`, already listed in the project's `requirements.txt`. For a
minimal terminal setup in a fresh checkout, run these commands from the project
root (Python 3.7.1 to 3.10, as recommended by the main README):

```bash
python3 -m venv venv
. venv/bin/activate
python3 -m pip install requests
cp config-template.json config.json
```

Enable the setting above, then run:

```bash
python3 app.py
```

At the terminal prompt, enter:

```text
/search Python asyncio documentation
```

The bot returns up to three results, each with a title, URL and excerpt. Search
results are returned directly, without calling a language model or adding them to
conversation history. Ordinary messages still use your selected model and need
its usual dependencies and credentials. Existing channels can use the same
command after their normal mention/prefix rules. Streaming callers receive one
complete search reply.

Only explicit `/search` commands send a query to `https://search.parallel.ai/mcp`.
Model credentials are not sent. Each HTTP request has a 5-second connection
timeout and a 30-second read timeout; failures produce an unavailable message
without automatic retries or a fallback model call. Set the setting to `false`
and restart the app to disable the command.

For the offline plugin/bridge tests, run from the project root:

```bash
python3 -m unittest discover -s tests -p 'test_parallel_search.py'
```
