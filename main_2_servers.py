"""Main 2: the loop as a client of every server. All of their tools are declared."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox, connect
from src.agent.trace import Trace
from src.desk.prompts import LEAD
from src.servers.data import SEED

TICKET = sys.argv[1] if len(sys.argv) > 1 else SEED["tickets"]["T-5001"]


def main():
    clients = connect()                    # one client per server: tools/list on each
    tools = Toolbox()
    for client in clients.values():
        tools.add_remote(client)           # every tool of every server

    model, trace = Model(), Trace()
    contents = [user_message(TICKET)]
    answer = run(model, LEAD, contents, tools, trace)

    print("\nanswer:", answer)
    first = trace.turns[0]["prompt_tokens"]
    print(f"declared tools: {len(tools.declarations())}   first request: {first:,} tokens")
    trace.summary()


main()
