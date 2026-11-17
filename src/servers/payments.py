"""The payments server, run by the payments team.  uv run python -m src.servers.payments

The refund rules live here, in the payments team's code: the limit, the balance, and the key
that makes a refund happen at most once per charge. No agent can change them."""
import os, sqlite3, time

from src.mcp.server import Server
from src.servers.data import SEED, STATE

server = Server("payments")
LIMIT_CENTS = 5000


def db():
    os.makedirs(STATE, exist_ok=True)
    conn = sqlite3.connect(os.path.join(STATE, "payments.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS refunds (refund_id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE,"
                 " charge_id TEXT, amount_cents INTEGER, reason TEXT, approved_by TEXT, at TEXT)")
    return conn


CHARGES = {c["charge_id"]: c for c in SEED["charges"]}


@server.tool("The charges on an order: id, amount in cents, status, time, checkout request.", read_only=True)
def get_charges(order_id: str) -> dict:
    return {"order_id": order_id, "charges": [c for c in CHARGES.values() if c["order_id"] == order_id]}


@server.tool("The refunds already made on a charge.", read_only=True)
def get_refunds(charge_id: str) -> dict:
    with db() as conn:
        rows = conn.execute("SELECT * FROM refunds WHERE charge_id = ?", (charge_id,)).fetchall()
    return {"charge_id": charge_id, "refunds": [dict(r) for r in rows]}


@server.tool("The card on file for a customer.", read_only=True)
def get_payment_method(customer_id: str) -> dict:
    return {"customer_id": customer_id, "card": SEED["customers"].get(customer_id, {}).get("card")}


@server.tool("Refund a captured charge, in cents. Refuses more than $50.00 (those need a person's "
             "approval), more than was paid, or a charge already refunded.", destructive=True, idempotent=True)
def issue_refund(charge_id: str, amount_cents: int, reason: str) -> dict:
    if amount_cents > LIMIT_CENTS:
        return {"error": f"over_limit: {amount_cents} cents is over the {LIMIT_CENTS}-cent limit; "
                         "a person must approve this refund"}
    return refund(charge_id, amount_cents, reason, approved_by=None)


@server.tool("Refund a charge a person has approved. For the approval path only.", destructive=True, idempotent=True)
def issue_approved_refund(charge_id: str, amount_cents: int, approved_by: str) -> dict:
    if not approved_by:
        return {"error": "approved_by is required"}
    return refund(charge_id, amount_cents, "approved", approved_by)


def refund(charge_id, amount_cents, reason, approved_by):
    charge = CHARGES.get(charge_id)
    if not charge or charge["status"] != "captured":
        return {"error": f"not_refundable: {charge_id} is not a captured charge"}
    if amount_cents <= 0 or amount_cents > charge["amount_cents"]:
        return {"error": f"bad_amount: {charge_id} was {charge['amount_cents']} cents"}
    key = f"refund:{charge_id}"                      # one refund per charge, however often asked
    with db() as conn:
        seen = conn.execute("SELECT * FROM refunds WHERE idempotency_key = ?", (key,)).fetchone()
        if seen:
            return {**dict(seen), "repeated": True}
        row = {"refund_id": f"r_{charge_id[3:]}", "idempotency_key": key, "charge_id": charge_id,
               "amount_cents": amount_cents, "reason": reason, "approved_by": approved_by,
               "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        conn.execute("INSERT INTO refunds VALUES (:refund_id, :idempotency_key, :charge_id, :amount_cents,"
                     " :reason, :approved_by, :at)", row)
    return {**row, "repeated": False}


@server.tool("Capture an authorized payment for an order.", destructive=True)
def capture_payment(order_id: str) -> dict:
    return {"error": "capture_payment is not available in this lab"}


if __name__ == "__main__":
    server.serve_stdio()
