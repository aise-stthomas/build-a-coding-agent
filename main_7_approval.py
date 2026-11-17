"""Main 7: a refund over the limit waits for a person. The process exits; approve.py resumes it.

  uv run main_7_approval.py
  uv run approve.py <run_id>
"""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.runs import Runs
from src.agent.toolbox import connect
from src.agent.trace import Trace
from src.desk.durable import REQUEST_APPROVAL, approval_tool, checkpoint, lead_tools
from src.desk.plan import Plan
from src.desk.prompts import APPROVAL, LEAD_WITH_WORKERS, PLAN
from src.servers.data import SEED

TICKET = sys.argv[1] if len(sys.argv) > 1 else SEED["tickets"]["T-5002"]


def main():
    clients = connect()
    model, trace, plan, runs = Model(), Trace(), Plan(), Runs()
    run_id = runs.create(TICKET)
    print("run:", run_id)

    lead = lead_tools(model, clients, trace, plan)
    lead.add(REQUEST_APPROVAL, approval_tool(runs, run_id, lead))  # a row; the run pauses

    contents = [user_message(TICKET)]
    answer = run(model, LEAD_WITH_WORKERS + PLAN + APPROVAL, contents, lead, trace,
                 prepare=plan.render, after_step=checkpoint(runs, run_id, plan))

    print("\nanswer:", answer)
    if lead.paused:
        print("\nThe run is a row now; no process is waiting.")
        print(f"Decide with: uv run approve.py {run_id}")


main()
