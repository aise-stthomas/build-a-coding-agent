"""The orders server, run by the commerce team.  uv run python -m src.servers.orders"""
from src.mcp.server import Server
from src.servers.data import SEED

server = Server("orders")
ORDERS = {o["order_id"]: o for o in SEED["orders"]}


@server.tool("Search a customer's orders, newest first. Optionally filter by status.", read_only=True)
def search_orders(customer_id: str, status: str = "") -> dict:
    found = [o for o in ORDERS.values() if o["customer_id"] == customer_id and (not status or o["status"] == status)]
    found.sort(key=lambda o: o["created_at"], reverse=True)
    return {"orders": [{k: o[k] for k in ("order_id", "created_at", "status", "total_cents")} for o in found]}


@server.tool("Find one order by its number: customer, items, total in cents, status.", read_only=True)
def find_order(order_id: str) -> dict:
    if order_id not in ORDERS:
        return {"error": f"no order {order_id}"}
    return ORDERS[order_id]


@server.tool("List the changes made to an order, oldest first.", read_only=True)
def get_order_history(order_id: str) -> dict:
    return {"order_id": order_id, "history": [{"at": a, "change": c} for a, c in SEED["order_history"].get(order_id, [])]}


@server.tool("Cancel an order that has not shipped.", destructive=True)
def cancel_order(order_id: str, reason: str) -> dict:
    return {"error": "cancel_order is not available in this lab"}


@server.tool("Change the shipping address of an order that has not shipped.")
def update_shipping_address(order_id: str, address: str) -> dict:
    return {"error": "update_shipping_address is not available in this lab"}


if __name__ == "__main__":
    server.serve_stdio()
