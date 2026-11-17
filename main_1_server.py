"""Main 1: a tool server and a client that talks to it. No model, no key."""
import json, sys

from src.mcp.client import Client


def show(label, message):
    print(f"\n{label}\n  {json.dumps(message)[:700]}")


def main():
    # Start the payments server as a process. Talk to it over stdin and stdout.
    command = [sys.executable, "-m", "src.servers.payments"]
    payments = Client("payments", command=command)

    # Discovery: what tools does this server have?
    tools = payments.list_tools()
    for t in tools:
        print(f"  {t['name']:<22} {t['description'][:70]}")

    # Invocation: run one, on the server.
    charges = payments.call_tool("get_charges", {"order_id": "88213"})
    show("get_charges(order_id='88213') returned:", charges)

    payments.close()


main()
