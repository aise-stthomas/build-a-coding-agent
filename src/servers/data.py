"""The desk's seeded data, and where each team keeps its state."""
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = json.load(open(os.path.join(ROOT, "data", "desk", "seed.json")))
STATE = os.environ.get("DESK_STATE", os.path.join(ROOT, "data", "state"))


def checkout_events(order_id):
    """The platform team's log for one order: the checkout itself, and everything else the
    site recorded for that session. Deterministic, so every run sees the same lines."""
    key = {"88213": ("2026-11-12T14:0", "req_a"), "90117": ("2026-11-13T09:4", "req_b"),
           "77310": ("2026-11-15T18:2", "req_c")}
    if order_id not in key:
        return []
    rng = random.Random(order_id)
    noise = ["cart.view", "recommendation.render", "session.heartbeat", "inventory.check",
             "price.quote", "page.view /checkout", "analytics.beacon", "feature_flag.eval"]
    lines = [{"at": f"{key[order_id][0]}0:{s:02d}Z", "event": rng.choice(noise), "order_id": order_id}
             for s in range(60) for _ in range(rng.randint(10, 30))]
    story = {
        "88213": [("14:02:09", "checkout.submit", "req_a1"), ("14:02:10", "payment.capture.requested", "req_a1"),
                  ("14:02:12", "payment.capture.succeeded ch_7730", "req_a1"),
                  ("14:02:19", "gateway.timeout waiting for capture response (10s)", "req_a1"),
                  ("14:02:19", "checkout.retry with a new idempotency key", "req_a2"),
                  ("14:02:21", "payment.capture.succeeded ch_7731", "req_a2"), ("14:02:22", "order.confirmed", "req_a2")],
        "90117": [("09:41:03", "checkout.submit", "req_b1"), ("09:41:06", "payment.capture.succeeded ch_9001", "req_b1"),
                  ("09:41:14", "gateway.timeout waiting for capture response (8s)", "req_b1"),
                  ("09:41:14", "checkout.retry with a new idempotency key", "req_b2"),
                  ("09:41:18", "payment.capture.succeeded ch_9002", "req_b2"), ("09:41:19", "order.confirmed", "req_b2")],
        "77310": [("18:20:00", "checkout.submit", "req_c1"), ("18:20:05", "payment.authorized au_6609", "req_c1"),
                  ("18:20:06", "order.confirmed", "req_c1")],
    }[order_id]
    day = key[order_id][0][:11]
    for at, event, request_id in story:
        lines.append({"at": f"{day}{at}Z", "event": event, "order_id": order_id, "request_id": request_id})
    return sorted(lines, key=lambda l: l["at"])
