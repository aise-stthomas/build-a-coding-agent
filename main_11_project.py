"""Main 11: what the agent knows before it reads a file. The project file in every request,
skills by description, and an explorer that reads in its own context."""
import sys

from dotenv import load_dotenv
load_dotenv()

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import Toolbox
from src.agent.trace import Trace
from src.coder.context import (EXPLORE, INSTRUCTIONS, LOAD_SKILL, explorer, project_file,
                               skill_list, skill_loader)
from src.coder.guard import Permissions, guarded
from src.coder.tools import Workspace

REQUEST = sys.argv[1] if len(sys.argv) > 1 else (
    "Add support for discount codes to checkout: a function that applies a code from "
    "src/checkout/codes.py to a cart's subtotal. Write tests for it.")


def main():
    workspace = Workspace()
    model, trace = Model(), Trace()
    tools = Toolbox()
    for declaration, fn in workspace.tools():
        tools.add(declaration, fn)
    tools.add(LOAD_SKILL, skill_loader(workspace))              # a skill's text, when named
    tools.add(EXPLORE, explorer(model, workspace, trace))       # reads in its own context
    guarded(tools, workspace, Permissions())

    system = INSTRUCTIONS + project_file(workspace) + skill_list(workspace)
    answer = run(model, system, [user_message(REQUEST)], tools, trace, max_steps=30)

    print("\nanswer:", answer)
    trace.summary()


main()
