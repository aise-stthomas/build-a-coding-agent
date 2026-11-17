# Lab: build a coding agent

A coding agent from scratch: a few general tools, the loop, rules around every call, and what
the agent knows before it reads a file. It calls the model by plain HTTP, so the code is the
wire format.

## Setup

```bash
uv sync
cp .env.example .env          # paste your Gemini key
uv run reset.py               # workspace/: a fresh copy of the broken repository
```

## Where everything is

| Path | What it is |
|---|---|
| `src/agent/` | the loop, the model, the trace, the toolbox |
| `src/coder/tools.py` | the agent's tools: read a file, search, edit by exact string, write a file, run a command |
| `src/coder/guard.py` | the permission rules and the hooks, checked around every call |
| `src/coder/context.py` | the instructions, the project file, skills, the explorer |
| `permissions.toml` | the deny and allow rules |
| `data/sample-repo/` | a small checkout module whose tests fail, on purpose. `reset.py` copies it to `workspace/` |
| `try_a_server_rpc_raw.py`, `try_a_server_mcp.py` | two ways to talk to a public MCP server (section 4) |

## Section 1 · A broken repository, fixed by an agent

The repository in `workspace/` is broken on purpose: some of its tests fail.

```bash
uv run pytest -q workspace       # the tests: 2 fail
uv run main_1_coder.py           # the agent finds the bug and fixes it
uv run pytest -q workspace       # the tests again
git -C workspace diff            # what the agent changed
```

1. Before you run the agent, read the failing tests and find the bug yourself. Where is it?
2. Watch the agent's turns. Which tools did it call, in what order, before it edited anything?
3. Read the diff. Is the fix the one you would have made? Read `workspace/AGENT.md`, the
   repository's project file. Does the fix follow it?

## Section 2 · Follow the agent

Each main is complete. Compare it with the one before, for example
`diff main_1_coder.py main_2_permissions.py`.

| Main | Command | What it adds |
|---|---|---|
| 1 | `uv run main_1_coder.py` | a coding agent: five general tools and the loop |
| 2 | `uv run main_2_permissions.py` | permissions and hooks around every call |
| 3 | `uv run reset.py --fixed`, then `uv run main_3_project.py` | the project file, skills, an explorer |

Main 2 asks you before any command no rule allows. Try
`uv run main_2_permissions.py "Fix the failing test, then commit and push."` and answer `n` to
the push. Run `uv run reset.py` between mains to start the repository over.

## Section 3 · Build on it

1. **Add a tool.** Give `Workspace` in `src/coder/tools.py` a `list_tests()` tool that returns
   the test names in `tests/`. Run Main 1 and see whether it is used.
2. **Add a rule.** In `permissions.toml`, allow `run(git push*)` for a branch named `agent/*`
   only. Run Main 2 and answer `y` or `n` when asked. What does the agent do after a no?
3. **Add a hook.** In `src/coder/guard.py`, add a before-call hook that refuses any
   `write_file` to `tests/` once a test file exists there. Run Main 3 and look for the refusal.
4. **Break it yourself.** Put a different bug in `data/sample-repo/src/checkout/cart.py`, run
   `uv run reset.py`, and see whether the agent finds it.

## Section 4 · An MCP server you did not write

DeepWiki runs a public MCP server, `https://mcp.deepwiki.com/mcp`: no login, no key, no model.
It answers questions about public GitHub repositories. Two scripts send it the same requests,
two ways:

```bash
uv run try_a_server_rpc_raw.py      # by hand: raw JSON-RPC over HTTP, every byte visible
uv run try_a_server_mcp.py          # through the official MCP Python SDK
```

Each sends `server/discover` (the SDK does it when it connects), `tools/list`, `prompts/list`,
`resources/list`, and one `tools/call`. Both take the same options:

| Option | What it does |
|---|---|
| `--repo owner/name [...]` | which public GitHub repositories (one, or several for `--ask`) |
| `--ask "question"` | calls `ask_wiki_question`: an answer about the code, citing files |
| `--contents` | calls `read_wiki_contents`: the repository's whole generated documentation |
| `--discover-only` | only the discovery methods, no tool call |
| `--chars N` | how much of a tool's answer to print (default 1500) |

With no `--ask` or `--contents`, the call is `read_wiki_structure`, the outline of the
documentation. Questions to try (an answer takes about 15 seconds):

```bash
uv run try_a_server_mcp.py --repo pytorch/pytorch
uv run try_a_server_mcp.py --repo pytorch/pytorch --ask "How does autograd record the operations on a tensor?"
uv run try_a_server_mcp.py --repo meta-llama/llama --ask "How are rotary position embeddings applied to queries and keys?"
uv run try_a_server_mcp.py --repo pytorch/pytorch meta-llama/llama --ask "How does each one implement scaled dot-product attention?"
```

The same options work with `try_a_server_rpc_raw.py`.

1. Which methods return anything? Which tools does the server offer, and what arguments do they take?
2. Read `try_a_server_rpc_raw.py`. What does every request carry besides the method and its
   arguments? Find the same things in `try_a_server_mcp.py`. Where did they go?
3. Remove the `Mcp-Method` header from the raw script and run it again. What does the server say?
4. Ask a question about a repository you use at work or in another course. Check one claim in
   the answer against the code it cites.

## Keep

The tools Main 1 called before its first edit, the diff it made, one command your permission
rules asked about with what happened next, and one answer from the public server with the
claim you checked.
