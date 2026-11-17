"""What a coding agent knows before it reads a file: the project file, and the skills' descriptions.
A skill's full text enters the context only when it is loaded."""
import os, re

from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.toolbox import Toolbox

INSTRUCTIONS = """You are a coding agent working in a repository. Use the tools to read, search,
edit and run commands. Read a file before you edit it. Run the tests after every change. Do not
change tests to make them pass unless the request asks for new tests. When a question needs
several files read, hand it to explore rather than reading them yourself. Finish with two or three
sentences: what was wrong or what was asked, what you changed, and the test result."""


def project_file(workspace):
    path = os.path.join(workspace.root, "AGENT.md")
    if not os.path.exists(path):
        return ""
    return "\n\nThe repository's project file, AGENT.md:\n" + open(path).read()


def skills(workspace):
    """name -> (description, path) for every skills/<name>/SKILL.md."""
    found = {}
    folder = os.path.join(workspace.root, "skills")
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        path = os.path.join(folder, name, "SKILL.md")
        text = open(path).read()
        description = re.search(r"^description:\s*(.+)$", text, re.M).group(1)
        found[name] = (description, path)
    return found


def skill_list(workspace):
    lines = [f"- {n}: {d}" for n, (d, _) in skills(workspace).items()]
    return ("\n\nSkills: load the one that covers a task with load_skill(name) before you start it.\n"
            + "\n".join(lines)) if lines else ""


LOAD_SKILL = {"name": "load_skill", "description": "Load a skill's full instructions by name.",
              "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}


def skill_loader(workspace):
    def load_skill(name):
        found = skills(workspace)
        if name not in found:
            return {"error": f"no skill {name}. Skills: {', '.join(found)}"}
        return {"skill": name, "text": open(found[name][1]).read()}
    return load_skill


EXPLORE = {"name": "explore",
           "description": "Hand a question about the code to an explorer that reads and searches in its "
                          "own context and returns paths, line numbers and a short answer.",
           "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}}

EXPLORER = """You answer one question about a repository by reading and searching. You cannot
change anything. Answer in at most eight lines: the paths and line numbers that matter, and what
they do."""


def explorer(model, workspace, trace):
    def explore(question):
        tools = Toolbox()
        for d, fn in workspace.tools():
            if d["name"] in ("read_file", "search"):           # read-only
                tools.add(d, fn)
        answer = run(model, EXPLORER, [user_message(question)], tools, trace, agent="explorer", max_steps=8)
        return {"answer": answer}
    return explore
