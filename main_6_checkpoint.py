"""Main 6: write the run down after every step. Kill the process; resume it with resume.py.

  uv run main_6_checkpoint.py --crash-after 2
  uv run main_6_checkpoint.py --crash-after-effect issue_refund
"""
import argparse

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.runs import Runs
from src.agent.toolbox import connect
from src.agent.trace import Trace
from src.desk.durable import checkpoint, crash_after_effect, lead_tools
from src.desk.plan import Plan
from src.desk.prompts import LEAD_WITH_WORKERS, PLAN
from src.servers.data import SEED

ap = argparse.ArgumentParser()
ap.add_argument("ticket", nargs="?", default=SEED["tickets"]["T-5001"])
ap.add_argument("--crash-after", type=int, help="exit after this step's checkpoint")
ap.add_argument("--crash-after-effect", help="exit right after this tool runs, before the checkpoint")
args = ap.parse_args()


def main():
    clients = connect()
    model, trace, plan, runs = Model(), Trace(), Plan(), Runs()
    run_id = runs.create(args.ticket)                             # the run is a row
    print("run:", run_id)

    lead = lead_tools(model, clients, trace, plan)                # Main 5's tools
    if args.crash_after_effect:
        lead.after_call = crash_after_effect(args.crash_after_effect, run_id)

    contents = [user_message(args.ticket)]
    answer = run(model, LEAD_WITH_WORKERS + PLAN, contents, lead, trace,
                 prepare=plan.render,
                 after_step=checkpoint(runs, run_id, plan, args.crash_after))  # every step

    print("\nanswer:", answer)


main()
