"""Main 2: permissions and hooks around every call. Deny wins, allow runs, anything else asks.

  uv run main_10_permissions.py "Fix the failing test, then commit and push."
"""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox
from src.agent.trace import Trace
from src.coder.context import INSTRUCTIONS
from src.coder.guard import Permissions, guarded
from src.coder.tools import Workspace

REQUEST = sys.argv[1] if len(sys.argv) > 1 else "Fix the failing test, then commit and push."


def main():
    workspace = Workspace()
    tools = Toolbox()
    for declaration, fn in workspace.tools():
        tools.add(declaration, fn)
    guarded(tools, workspace, Permissions())      # every call: permissions, then hooks

    model, trace = Model(), Trace()
    answer = run(model, INSTRUCTIONS, [user_message(REQUEST)], tools, trace, max_steps=20)

    print("\nanswer:", answer)
    trace.summary()


main()
