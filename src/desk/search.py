"""Searching for tools: the declarations are documents in an index; a search adds the best few
to the next request. A plain word-overlap score is enough at this size."""
import re

from src.agent.toolbox import for_model

FIND_TOOLS = {
    "name": "find_tools",
    "description": "Search the available tools by what they do. query: a few words. "
                   "The best matches are added to your tools for the next turn.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
}


def words(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z]+", text.lower()) if len(w) > 2}


def tool_search(toolbox, clients, k=3):
    index = [(c, d) for c in clients.values() for d in c.tools if d["name"] in c.allow]

    def find_tools(query):
        q = words(query)
        scored = sorted(index, key=lambda cd: -len(q & words(cd[1]["name"].replace("_", " ") + " " + cd[1]["description"])))
        found = [(c, d) for c, d in scored[:k] if q & words(d["name"].replace("_", " ") + " " + d["description"])]
        for c, d in found:
            if d["name"] not in toolbox.remote:
                toolbox.add_remote(c, [d["name"]])
        return {"added": [{"name": d["name"], "description": d["description"]} for _, d in found]}

    return find_tools
