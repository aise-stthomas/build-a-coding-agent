"""Main 8: keep each request inside a budget. Long results are cut and kept in a file; when a
request would still pass the budget, older turns are sent as a summary.

  uv run main_8_compact.py --budget 6000
"""
import argparse

from dotenv import load_dotenv
load_dotenv()

from src.agent.compact import Compactor, cut
from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox, connect
from src.agent.trace import Trace
from src.desk.prompts import LEAD
from src.servers.data import SEED

ap = argparse.ArgumentParser()
ap.add_argument("ticket", nargs="?", default=SEED["tickets"]["T-5001"])
ap.add_argument("--budget", type=int, default=6000, help="tokens per request, roughly")
args = ap.parse_args()


def main():
    clients = connect()
    model, trace = Model(), Trace()

    tools = Toolbox()                                  # one loop, the allowed tools
    for client in clients.values():
        tools.add_remote(client, client.allow)
    call = tools.call
    tools.call = lambda name, a: cut(name, call(name, a))           # cut long results

    contents = [user_message(args.ticket)]
    answer = run(model, LEAD, contents, tools, trace,
                 prepare=Compactor(model, args.budget, trace))      # summary when over budget

    print("\nanswer:", answer)
    sizes = [t["prompt_tokens"] for t in trace.turns if t["agent"] == "lead"]
    print("request sizes:", sizes)
    trace.summary()


main()
