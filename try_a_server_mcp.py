"""The same requests as try_a_server_rpc_raw.py, through the official MCP Python SDK.

The SDK writes the JSON-RPC messages, the _meta fields and the HTTP headers for you, discovers
the server when it connects, and falls back to the older initialize handshake for a server that
needs it. Compare it with the raw version: the requests on the wire are the same.

Options (the same in both scripts):
  --repo owner/name [...]     which public GitHub repositories (default: the MCP specification's own)
  --ask "question"            ask_wiki_question: a question about the repositories (several are fine)
  --contents                  read_wiki_contents: the repository's whole generated documentation
  --discover-only             only the discovery methods, no tool call
  --chars N                   print at most N characters of a tool's answer (default 1500)
  --url <server URL>          another server that speaks 2026-07-28 (default: DeepWiki)

With no --ask or --contents, the call is read_wiki_structure: the outline of the documentation.

Try:
  uv run try_a_server_mcp.py --repo pytorch/pytorch
  uv run try_a_server_mcp.py --repo pytorch/pytorch --ask "How does autograd record the operations on a tensor?"
  uv run try_a_server_mcp.py --repo meta-llama/llama --ask "How are rotary position embeddings applied to queries and keys?"
  uv run try_a_server_mcp.py --repo pytorch/pytorch meta-llama/llama --ask "How does each one implement scaled dot-product attention?"
"""
import argparse, asyncio, json

from mcp import Client

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--url", default="https://mcp.deepwiki.com/mcp")
ap.add_argument("--repo", nargs="+", default=["modelcontextprotocol/modelcontextprotocol"])
ap.add_argument("--ask", metavar="QUESTION")
ap.add_argument("--contents", action="store_true")
ap.add_argument("--discover-only", action="store_true")
ap.add_argument("--chars", type=int, default=1500)
args = ap.parse_args()


def which_call():
    """The tool and arguments the options ask for, or None."""
    if args.discover_only:
        return None
    if args.ask:
        return "ask_wiki_question", {"repoName": args.repo if len(args.repo) > 1 else args.repo[0],
                                     "question": args.ask}
    if args.contents:
        return "read_wiki_contents", {"repoName": args.repo[0]}
    return "read_wiki_structure", {"repoName": args.repo[0]}


async def main():
    async with Client(args.url) as client:            # connecting does server/discover
        print("\n== connected: which version, which server, which capabilities")
        print(f"  protocol version: {client.protocol_version}")
        print(f"  server: {client.server_info.name if client.server_info else '?'}")
        print(f"  capabilities: {client.server_capabilities.model_dump(exclude_none=True)}")

        tools = (await client.list_tools()).tools      # tools/list
        print(f"\n== tools/list: {len(tools)} tools")
        for t in tools:
            print(f"  {t.name:<24} {(t.description or '')[:80]}")
            print(f"  {'':<24} arguments: {', '.join(t.input_schema.get('properties', {}))}")

        prompts = (await client.list_prompts()).prompts          # prompts/list
        resources = (await client.list_resources()).resources  # resources/list
        print(f"\n== prompts/list: {len(prompts)} prompts    resources/list: {len(resources)} resources")

        call = which_call()
        if call:
            name, arguments = call
            result = await client.call_tool(name, arguments)       # tools/call
            text = "".join(getattr(c, "text", "") for c in result.content)
            print(f"\n== tools/call {name}({json.dumps(arguments)})   isError: {result.is_error}")
            print("  " + text[:args.chars].replace("\n", "\n  ") + ("\n  ..." if len(text) > args.chars else ""))


asyncio.run(main())
