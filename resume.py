"""Resume a run from its row: rebuild the contents and the plan, carry out any decision,
and continue the loop from the next step.   uv run resume.py <run_id>"""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.model import Model
from src.agent.runs import Runs
from src.agent.toolbox import connect
from src.agent.trace import Trace
from src.desk.durable import REQUEST_APPROVAL, apply_decisions, approval_tool, checkpoint, lead_tools
from src.desk.plan import Plan
from src.desk.prompts import APPROVAL, LEAD_WITH_WORKERS, PLAN


def resume(run_id):
    runs = Runs()
    row = runs.load(run_id)
    if row["status"] == "done":
        print(f"{run_id} is done. Nothing to resume.")
        return
    print(f"resuming {run_id} after step {row['step']} ({row['status']})")

    clients = connect()
    model, trace, plan = Model(), Trace(), Plan(row["plan"])
    contents = row["contents"]
    apply_decisions(runs, run_id, clients, contents)

    lead = lead_tools(model, clients, trace, plan)
    lead.add(REQUEST_APPROVAL, approval_tool(runs, run_id, lead))
    answer = run(model, LEAD_WITH_WORKERS + PLAN + APPROVAL, contents, lead, trace,
                 prepare=plan.render, after_step=checkpoint(runs, run_id, plan),
                 first_step=row["step"] + 1)
    print("\nanswer:", answer)
    print("model calls in this process:", len(trace.turns))


if __name__ == "__main__":
    resume(sys.argv[1])
