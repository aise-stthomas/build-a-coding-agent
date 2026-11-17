"""The smallest tool server: one tool, served over HTTP on this machine, with the MCP SDK.

  uv run hello_server.py          in one terminal: it prints a line for every call it answers
  uv run try_a_server_mcp.py --url http://127.0.0.1:8000/mcp --tool say_hello --args '{"name": "Ana"}'
                                  in another: the reply names this server's process and call count
"""
import datetime, os

from mcp.server import MCPServer

server = MCPServer("hello")
calls = 0


@server.tool(description="Say hello to someone. The reply says which server process answered.")
def say_hello(name: str) -> str:
    global calls
    calls += 1
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[hello server, process {os.getpid()}] tools/call say_hello(name={name!r}): call {calls} at {now}",
          flush=True)
    return f"Hello, {name}! From the hello server, process {os.getpid()}, call {calls}, at {now}."


if __name__ == "__main__":
    print(f"hello server: process {os.getpid()}, listening at http://127.0.0.1:8000/mcp. Ctrl-C stops it.",
          flush=True)
    server.run("streamable-http", host="127.0.0.1", port=8000)
