"""Main 3: only some tools in each request. Allow lists, and a search for tools."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox, connect
from src.agent.trace import Trace
from src.desk.prompts import LEAD, SEARCH
from src.desk.search import FIND_TOOLS, tool_search
from src.servers.data import SEED

TICKET = sys.argv[1] if len(sys.argv) > 1 else SEED["tickets"]["T-5001"]


def main():
    clients = connect()
    tools = Toolbox()
    # Declared at the start: one search tool. It finds among the allowed tools only.
    tools.add(FIND_TOOLS, tool_search(tools, clients))

    model, trace = Model(), Trace()
    contents = [user_message(TICKET)]
    answer = run(model, LEAD + SEARCH, contents, tools, trace)

    print("\nanswer:", answer)
    print(f"declared at the end: {[d['name'] for d in tools.declarations()]}")
    print(f"first request: {trace.turns[0]['prompt_tokens']:,} tokens")
    trace.summary()


main()
