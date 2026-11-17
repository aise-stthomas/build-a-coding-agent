"""Runs that outlast a process: a checkpoint after every step, resume from the row, and a
person's approval as a row the run waits on."""
import os, sys

from src.agent.messages import user_message
from src.agent.toolbox import Toolbox
from src.desk.plan import UPDATE_PLAN
from src.desk.workers import INVESTIGATE, investigator

REQUEST_APPROVAL = {
    "name": "request_approval",
    "description": "Ask a person to approve a refund over 5000 cents. The run waits for the decision.",
    "parameters": {"type": "object", "properties": {
        "charge_id": {"type": "string"}, "amount_cents": {"type": "integer"}, "note": {"type": "string"}},
        "required": ["charge_id", "amount_cents", "note"]},
}


def lead_tools(model, clients, trace, plan):
    """The lead's tools from Main 5: workers, the one refund tool, the plan."""
    lead = Toolbox()
    lead.add(INVESTIGATE, investigator(model, clients, trace))
    lead.add_remote(clients["payments"], ["issue_refund"])
    lead.add(UPDATE_PLAN, plan.update)
    return lead


def checkpoint(runs, run_id, plan, crash_after=None):
    def after_step(step, contents, status):
        runs.save(run_id, step, status, contents, plan.steps)    # the run, written down
        print(f"  [checkpoint] {run_id} step {step} {status}")
        if crash_after == step:
            print(f"\n  killed after step {step}. Resume with: uv run resume.py {run_id}")
            sys.stdout.flush()
            os._exit(1)
    return after_step


def crash_after_effect(tool_name, run_id):
    """Exit the moment a tool's effect has happened, before the checkpoint is written."""
    def after_call(name, args, result):
        if name == tool_name:
            print(f"\n  {name} returned {result}\n  killed before the checkpoint. "
                  f"Resume with: uv run resume.py {run_id}")
            sys.stdout.flush()
            os._exit(1)
    return after_call


def approval_tool(runs, run_id, toolbox):
    def request_approval(charge_id, amount_cents, note):
        approval_id = runs.request_approval(run_id, charge_id, amount_cents, note)
        toolbox.paused = True                    # the loop returns after this step
        return {"status": "waiting_for_approval", "approval_id": approval_id}
    return request_approval


def apply_decisions(runs, run_id, clients, contents):
    """On resume: carry out each decision under the approver's name, then tell the run."""
    for a in runs.decided_unapplied(run_id):
        if a["decision"] == "approved":
            result = clients["payments"].call_tool("issue_approved_refund", {
                "charge_id": a["charge_id"], "amount_cents": a["amount_cents"],
                "approved_by": a["decided_by"]})
            outcome = f"approved by {a['decided_by']}. Refund issued: {result}"
        else:
            outcome = f"declined by {a['decided_by']}. No refund was issued"
        runs.mark_applied(a["approval_id"])
        note = {"text": f"Approval {a['approval_id']} for {a['charge_id']}, {a['amount_cents']} cents: {outcome}"}
        if contents and contents[-1]["role"] == "user":
            contents[-1] = {"role": "user", "parts": contents[-1]["parts"] + [note]}
        else:
            contents.append(user_message(note["text"]))
        print(f"  [approval] {note['text']}")
