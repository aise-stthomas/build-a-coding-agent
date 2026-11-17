"""Main 4: a lead that hands work to workers. Each worker is a loop with its own context."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox, connect
from src.agent.trace import Trace
from src.desk.prompts import LEAD_WITH_WORKERS
from src.desk.workers import INVESTIGATE, investigator
from src.servers.data import SEED

TICKET = sys.argv[1] if len(sys.argv) > 1 else SEED["tickets"]["T-5001"]


def main():
    clients = connect()
    model, trace = Model(), Trace()

    lead = Toolbox()
    lead.add(INVESTIGATE, investigator(model, clients, trace))   # workers, behind one tool
    lead.add_remote(clients["payments"], ["issue_refund"])        # the one action

    contents = [user_message(TICKET)]
    answer = run(model, LEAD_WITH_WORKERS, contents, lead, trace)

    print("\nanswer:", answer)
    trace.summary()


main()
