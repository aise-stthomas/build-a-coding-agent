"""The payments server as a function behind a URL: Streamable HTTP, one POST per message.

Each request stands alone (no session), so any instance can answer any request. The refunds
live in the function's /tmp here, which a real deployment would replace with a database."""
import json, os

os.environ.setdefault("DESK_STATE", "/tmp/desk-state")

from src.mcp import protocol as p  # noqa: E402
from src.servers.payments import server  # noqa: E402


def handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
        return {"statusCode": 405, "body": "POST one JSON-RPC message"}
    message = json.loads(event.get("body") or "{}")
    reply = server.handle(message)
    if reply is None:
        return {"statusCode": 202, "body": ""}
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"},
            "body": json.dumps(reply)}
