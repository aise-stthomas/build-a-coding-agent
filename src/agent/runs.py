"""The run, written down. One row per run, rewritten after every step, so any process can
pick it up. Approvals are rows too: a run waiting for a person is data, not a process."""
import json, os, sqlite3, time, uuid

STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "state")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Runs:
    def __init__(self, path=os.path.join(STATE, "runs.db")):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, ticket TEXT, step INTEGER,
                status TEXT, contents TEXT, plan TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS approvals (approval_id TEXT PRIMARY KEY, run_id TEXT,
                charge_id TEXT, amount_cents INTEGER, note TEXT, requested_at TEXT,
                decided_by TEXT, decision TEXT, decided_at TEXT, applied INTEGER DEFAULT 0);""")

    def create(self, ticket):
        run_id = "run_" + uuid.uuid4().hex[:8]
        self.conn.execute("INSERT INTO runs VALUES (?, ?, 0, 'running', '[]', '[]', ?)", (run_id, ticket, now()))
        self.conn.commit()
        return run_id

    def save(self, run_id, step, status, contents, plan):
        self.conn.execute("UPDATE runs SET step=?, status=?, contents=?, plan=?, updated_at=? WHERE run_id=?",
                          (step, status, json.dumps(contents), json.dumps(plan), now(), run_id))
        self.conn.commit()

    def load(self, run_id):
        row = self.conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise SystemExit(f"no run {run_id}")
        return {**dict(row), "contents": json.loads(row["contents"]), "plan": json.loads(row["plan"])}

    def request_approval(self, run_id, charge_id, amount_cents, note):
        approval_id = "ap_" + uuid.uuid4().hex[:6]
        self.conn.execute("INSERT INTO approvals (approval_id, run_id, charge_id, amount_cents, note, requested_at)"
                          " VALUES (?, ?, ?, ?, ?, ?)", (approval_id, run_id, charge_id, amount_cents, note, now()))
        self.conn.commit()
        return approval_id

    def decide(self, run_id, decided_by, decision):
        self.conn.execute("UPDATE approvals SET decided_by=?, decision=?, decided_at=? WHERE run_id=? AND decision IS NULL",
                          (decided_by, decision, now(), run_id))
        self.conn.commit()

    def decided_unapplied(self, run_id):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM approvals WHERE run_id=? AND decision IS NOT NULL AND applied=0", (run_id,))]

    def mark_applied(self, approval_id):
        self.conn.execute("UPDATE approvals SET applied=1 WHERE approval_id=?", (approval_id,))
        self.conn.commit()
