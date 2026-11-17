"""The events server, run by the platform team.  uv run python -m src.servers.events"""
from src.mcp.server import Server
from src.servers.data import checkout_events

server = Server("events")


@server.tool("Every event the site logged for an order's checkout session, oldest first.", read_only=True)
def get_events(order_id: str) -> dict:
    lines = checkout_events(order_id)
    return {"order_id": order_id, "count": len(lines), "events": lines}


@server.tool("Search an order's events for a word, such as 'capture' or 'retry'.", read_only=True)
def search_events(order_id: str, query: str) -> dict:
    lines = [l for l in checkout_events(order_id) if query.lower() in l["event"].lower()]
    return {"order_id": order_id, "query": query, "count": len(lines), "events": lines}


@server.tool("Whether a platform service is healthy now.", read_only=True)
def get_service_status(service: str) -> dict:
    return {"service": service, "status": "healthy"}


if __name__ == "__main__":
    server.serve_stdio()
