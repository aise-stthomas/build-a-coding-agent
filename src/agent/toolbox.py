"""The toolbox: which tools a request declares, and where each call runs.

A tool is either local (a Python function in this process) or remote (a tool on a server,
reached through a client). The model sees the same declarations either way."""
import os, sys, tomllib
from concurrent.futures import ThreadPoolExecutor

from src.mcp.client import Client
from src.mcp.server import input_schema

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def connect(config="servers.toml"):
    """One client per server in the config; each keeps its allow lists."""
    clients = {}
    for name, spec in tomllib.load(open(os.path.join(ROOT, config), "rb")).items():
        url = os.environ.get(f"{name.upper()}_URL") or spec.get("url")
        command = [sys.executable if c == "python" else c for c in spec.get("command", [])]
        client = Client(name, command=None if url else command, url=url)
        client.allow, client.read = spec.get("allow", []), spec.get("read", [])
        client.tools = client.list_tools()           # discovery: tools/list
        clients[name] = client
    return clients


def declare(fn, description):
    """A local function as a declaration: the name and arguments come from its signature."""
    return {"name": fn.__name__, "description": description, "parameters": input_schema(fn)}


def for_model(declaration):
    """An MCP declaration, as the model's provider wants it."""
    return {"name": declaration["name"], "description": declaration["description"],
            "parameters": declaration["inputSchema"]}


class Toolbox:
    def __init__(self):
        self.local = {}        # name -> function in this process
        self.remote = {}       # name -> the client of the server that has it
        self.declared = []     # what the next request declares, in order
        self.paused = False    # set by a tool that hands the run to a person
        self.after_call = None # a hook the program may set: f(name, args, result)

    def add(self, declaration, fn):
        self.local[declaration["name"]] = fn
        self.declared.append(declaration)

    def add_remote(self, client, names=None):
        for d in client.tools:
            if names is None or d["name"] in names:
                self.remote[d["name"]] = client
                self.declared.append(for_model(d))

    def declarations(self):
        return self.declared

    def call(self, name, args):
        if name in self.local:
            result = self.local[name](**args)
        elif name in self.remote:
            result = self.remote[name].call_tool(name, args)
        else:
            result = {"error": f"Unknown tool: {name}. Available tools: "
                               f"{', '.join(d['name'] for d in self.declared)}"}
        if self.after_call:
            self.after_call(name, args, result)
        return result

    def call_all(self, calls):
        # Several calls named in one turn run at the same time.
        if len(calls) == 1:
            return [self.call(calls[0]["name"], calls[0]["args"])]
        with ThreadPoolExecutor(max_workers=len(calls)) as pool:
            return list(pool.map(lambda c: self.call(c["name"], c["args"]), calls))
