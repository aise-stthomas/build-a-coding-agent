"""The same requests as try_a_server_rpc_raw.py, through the official MCP Python SDK.

  uv run try_a_server_mcp.py                       DeepWiki's public server
  uv run try_a_server_mcp.py --repo owner/name     ask about another public GitHub repository
  uv run try_a_server_mcp.py --url <server URL>

The SDK writes the JSON-RPC messages, the _meta fields and the HTTP headers for you, discovers
the server when it connects, and falls back to the older initialize handshake for a server that
needs it. Compare it with the raw version: the requests on the wire are the same.
"""
import argparse, asyncio, json

from mcp import Client

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="https://mcp.deepwiki.com/mcp")
ap.add_argument("--repo", default="modelcontextprotocol/modelcontextprotocol")
args = ap.parse_args()


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
            print(f"  {'':<24} arguments: {json.dumps(t.input_schema.get('properties', {}))[:80]}")

        prompts = (await client.list_prompts()).prompts          # prompts/list
        resources = (await client.list_resources()).resources  # resources/list
        print(f"\n== prompts/list: {len(prompts)} prompts    resources/list: {len(resources)} resources")

        tool = next((t for t in tools if t.name == "read_wiki_structure"), None)
        if tool:
            arg = tool.input_schema["required"][0]
            result = await client.call_tool(tool.name, {arg: args.repo})   # tools/call
            text = "".join(getattr(c, "text", "") for c in result.content)
            print(f"\n== tools/call {tool.name}({arg}={args.repo!r})   isError: {result.is_error}")
            print("  " + text[:700].replace("\n", "\n  "))


asyncio.run(main())
