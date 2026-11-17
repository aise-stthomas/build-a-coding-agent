"""Main 9: a coding agent. A few general tools on a workspace; the same loop."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox
from src.agent.trace import Trace
from src.coder.context import INSTRUCTIONS
from src.coder.tools import Workspace

REQUEST = sys.argv[1] if len(sys.argv) > 1 else "The checkout tests fail. Find out why and fix it."


def main():
    workspace = Workspace()                       # a copy of data/sample-repo
    tools = Toolbox()
    for declaration, fn in workspace.tools():     # read, search, edit, write, run
        tools.add(declaration, fn)

    model, trace = Model(), Trace()
    answer = run(model, INSTRUCTIONS, [user_message(REQUEST)], tools, trace, max_steps=20)

    print("\nanswer:", answer)
    trace.summary()


main()
