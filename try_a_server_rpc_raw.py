"""Talk to a public MCP server you did not write, by hand: raw JSON-RPC over HTTP, no SDK.

It sends the discovery methods one at a time (server/discover, tools/list, prompts/list,
resources/list) and then one tools/call, printing what comes back. Every request carries its
protocol version and capabilities in _meta, and over HTTP the method also goes in a header.
try_a_server_mcp.py sends the same requests through the MCP SDK: compare the two.

Options (the same in both scripts):
  --repo owner/name [...]     which public GitHub repositories (default: the MCP specification's own)
  --ask "question"            ask_wiki_question: a question about the repositories (several are fine)
  --contents                  read_wiki_contents: the repository's whole generated documentation
  --discover-only             only the discovery methods, no tool call
  --chars N                   print at most N characters of a tool's answer (default 1500)
  --url <server URL>          another server that speaks 2026-07-28 (default: DeepWiki)
  --tool NAME --args JSON     call any tool by name, with its arguments as JSON

With no --ask or --contents, the call is read_wiki_structure: the outline of the documentation.

Try:
  uv run try_a_server_rpc_raw.py --repo pytorch/pytorch
  uv run try_a_server_rpc_raw.py --repo pytorch/pytorch --ask "How does autograd record the operations on a tensor?"
  uv run try_a_server_rpc_raw.py --repo meta-llama/llama --ask "How are rotary position embeddings applied to queries and keys?"
  uv run try_a_server_rpc_raw.py --repo pytorch/pytorch meta-llama/llama --ask "How does each one implement scaled dot-product attention?"
"""
import argparse, itertools, json, urllib.error, urllib.request

VERSION = "2026-07-28"
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--url", default="https://mcp.deepwiki.com/mcp")
ap.add_argument("--repo", nargs="+", default=["modelcontextprotocol/modelcontextprotocol"])
ap.add_argument("--ask", metavar="QUESTION")
ap.add_argument("--contents", action="store_true")
ap.add_argument("--discover-only", action="store_true")
ap.add_argument("--chars", type=int, default=1500)
ap.add_argument("--tool", help="call this tool instead of a DeepWiki one")
ap.add_argument("--args", default="{}", help="the tool's arguments, as JSON")
args = ap.parse_args()



def argument_types(schema):
    """Each argument and its JSON type, from a tool's inputSchema."""
    def kind(v):
        return " or ".join(x.get("type", "?") for x in v["anyOf"]) if "anyOf" in v else v.get("type", "any")
    return ", ".join(f"{k} ({kind(v)})" for k, v in schema.get("properties", {}).items())

def which_call():
    """The tool and arguments the options ask for, or None."""
    if args.discover_only:
        return None
    if args.tool:
        return args.tool, json.loads(args.args)
    if args.ask:
        return "ask_wiki_question", {"repoName": args.repo if len(args.repo) > 1 else args.repo[0],
                                     "question": args.ask}
    if args.contents:
        return "read_wiki_contents", {"repoName": args.repo[0]}
    return "read_wiki_structure", {"repoName": args.repo[0]}

ids = itertools.count(1)


def send(method, params=None):
    message = {"jsonrpc": "2.0", "id": next(ids), "method": method, "params": {
        **(params or {}),
        "_meta": {"io.modelcontextprotocol/protocolVersion": VERSION,
                  "io.modelcontextprotocol/clientCapabilities": {},
                  "io.modelcontextprotocol/clientInfo": {"name": "build-a-coding-agent", "version": "0.1.0"}}}}
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "MCP-Protocol-Version": VERSION}
    headers["Mcp-Method"] = method          # the method again, as a header: required over HTTP
    if method == "tools/call":
        headers["Mcp-Name"] = params["name"]
    req = urllib.request.Request(args.url, json.dumps(message).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
    except urllib.error.URLError as e:
        raise SystemExit(f"no server answered at {args.url}: {e.reason}. Is it running?")
    # A reply is either one JSON object or a short event stream whose data line holds it.
    for line in body.splitlines():
        if line.startswith("data:"):
            body = line[5:].strip()
    return json.loads(body)


def show(title, reply, keep=600):
    print(f"\n== {title}")
    print("  " + json.dumps(reply)[:keep])


show("server/discover: which versions, which capabilities", send("server/discover"))

reply = send("tools/list")
tools = reply.get("result", {}).get("tools", [])
print(f"\n== tools/list: {len(tools)} tools")
for t in tools:
    print(f"  {t['name']:<24} {t['description'][:80]}")
    print(f"  {'':<24} arguments: {argument_types(t['inputSchema'])}")

show("prompts/list", send("prompts/list"), 300)
show("resources/list", send("resources/list"), 300)

call = which_call()
if call:
    name, arguments = call
    reply = send("tools/call", {"name": name, "arguments": arguments})
    result = reply.get("result", {})
    text = "".join(c.get("text", "") for c in result.get("content", [])) or json.dumps(reply)
    print(f"\n== tools/call {name}({json.dumps(arguments)})   isError: {result.get('isError', False)}")
    print("  " + text[:args.chars].replace("\n", "\n  ") + ("\n  ..." if len(text) > args.chars else ""))
