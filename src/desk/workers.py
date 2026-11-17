"""A worker is a loop behind a tool: new contents, its own instructions, only the servers
the program allows, and its own step limit. The lead gets back a summary, not the results."""
from src.agent.loop import run
from src.agent.messages import user_message
from src.agent.toolbox import Toolbox
from src.desk.prompts import WORKER

INVESTIGATE = {
    "name": "investigate",
    "description": "Hand one investigation to a worker. task: one sentence. server: the one "
                   "system it may read: orders, payments or events. Returns the worker's summary.",
    "parameters": {"type": "object", "properties": {
        "task": {"type": "string"}, "server": {"type": "string"}},
        "required": ["task", "server"]},
}
SUMMARY_LIMIT = 1500


def investigator(model, clients, trace, max_steps=6):
    count = iter(range(1, 1000))

    def investigate(task, server):
        # The program decides what a worker can reach: one server, read tools only.
        if server not in clients:
            return {"error": f"unknown server: {server}. Known: {', '.join(clients)}"}
        tools = Toolbox()
        tools.add_remote(clients[server], clients[server].read)
        name = f"worker {next(count)} ({server})"
        contents = [user_message(task)]
        summary = run(model, WORKER, contents, tools, trace, agent=name,
                      max_steps=max_steps)
        return {"summary": summary[:SUMMARY_LIMIT], "worker": name,
                "input_tokens": trace.tokens(name)}

    return investigate
