# build-a-coding-agent

AI Systems Engineering lab. A coding agent, built from scratch: a few general tools (read,
search, edit, write, run), the loop, permissions and hooks around every call, and a project
file and skills. It starts on a repository whose tests fail, on purpose, and fixes it.

- No SDK for the model: plain HTTP to the Gemini API, so the code is the wire format.
- The instructions are in [LAB.md](LAB.md).

```bash
uv sync
cp .env.example .env          # your Gemini key
uv run reset.py               # workspace/: the broken repository
uv run pytest -q workspace    # 2 tests fail
uv run main_1_coder.py        # the agent fixes them
```

Also here: `try_a_server_rpc_raw.py` and `try_a_server_mcp.py` send the same requests to a
public MCP server, by hand and through the MCP SDK.
