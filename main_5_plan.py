"""Main 5: a plan the run writes with a tool, placed last in every request."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox, connect
from src.agent.trace import Trace
from src.desk.plan import UPDATE_PLAN, Plan
from src.desk.prompts import LEAD_WITH_WORKERS, PLAN
from src.desk.workers import INVESTIGATE, investigator
from src.servers.data import SEED

TICKET = sys.argv[1] if len(sys.argv) > 1 else SEED["tickets"]["T-5001"]


def main():
    clients = connect()
    model, trace, plan = Model(), Trace(), Plan()

    lead = Toolbox()
    lead.add(INVESTIGATE, investigator(model, clients, trace))
    lead.add_remote(clients["payments"], ["issue_refund"])
    lead.add(UPDATE_PLAN, plan.update)                            # the run writes the plan

    contents = [user_message(TICKET)]
    answer = run(model, LEAD_WITH_WORKERS + PLAN, contents, lead, trace,
                 prepare=plan.render)                             # the program places it

    print("\nanswer:", answer)
    print("\nthe plan at the end:\n  " + "\n  ".join(plan.steps))
    trace.summary()


main()
