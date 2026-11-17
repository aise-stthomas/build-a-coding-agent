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
| `try_a_server_rpc_raw.py`, `try_a_server_mcp.py` | two ways to talk to an MCP server (sections 4 and 5) |
| `hello_server.py` | the smallest MCP server: one tool, on your laptop (section 5) |

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
the push. The workspace's `origin` is a folder on your laptop, `data/state/origin.git`, so a
push you allow goes nowhere public: `git -C workspace ls-remote origin` shows what reached it.
Run `uv run reset.py` between mains to start the repository over.

## Section 3 · Build on it

1. **Add a tool.** Give `Workspace` in `src/coder/tools.py` a `list_tests()` tool that returns
   the test names in `tests/`, and add it to the list in `tools()`. Run Main 1 and see whether
   it is used. Main 2 will ask before calling it until you add `list_tests(*)` to the allow rules.
2. **Add a rule.** In `permissions.toml`, allow creating and pushing a branch named `agent/*`
   only: `run(git checkout -b agent/*)` and `run(git push origin agent/*)`. Then run
   `uv run main_2_permissions.py "Fix the failing test, commit it on a new branch named agent/fix-tax, and push that branch to origin."`
   and answer `n` to anything it asks. Which commands asked, and why did each one not match?
   What does the agent do after a no? Check what reached `origin`.
3. **Add a hook.** In `before_call` in `src/coder/guard.py`, refuse a `write_file` that would
   replace a file that already exists in `tests/` (`workspace.path(path)` gives its full path, as a string).
   Run `uv run reset.py --fixed` and Main 3, and look for the refusal. What does the agent do
   instead?
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

## Section 5 · Your own MCP server

`hello_server.py` is a tool server in a few lines: one tool, `say_hello(name)`, served over HTTP
on your laptop with the MCP SDK. Use two terminals.

```bash
uv run hello_server.py            # terminal 1: the server. Leave it running.
```

```bash
uv run try_a_server_mcp.py --url http://127.0.0.1:8000/mcp --tool say_hello --args '{"name": "Ana"}'
uv run try_a_server_rpc_raw.py --url http://127.0.0.1:8000/mcp --tool say_hello --args '{"name": "Raj"}'
```

Terminal 1 prints a line for every call it answers, and the reply names the server's process and
counts the calls, so you can see that your server did the work.

1. Find the server's process number in terminal 1 and in the reply. Run a client twice. What
   changes in the reply, and why?
2. Stop the server (Ctrl-C) and run a client again. What happens?
3. Add a second tool to `hello_server.py`, for example `add(a: int, b: int) -> int`. Restart the
   server and run `try_a_server_mcp.py --url http://127.0.0.1:8000/mcp --discover-only`. Does it
   list your tool? What arguments does it say the tool takes, and where did that come from?

## Keep

The tools Main 1 called before its first edit, the diff it made, one command your permission
rules asked about with what happened next, one answer from the public server with the claim
you checked, and the reply from your own server's second tool.
