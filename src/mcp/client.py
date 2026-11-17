"""A client: one connection to one tool server. No SDK, so the code is the wire format.

stdio: start the server as a process; write one JSON line, read one JSON line.
HTTP:  POST each message to the server's URL; the reply is the response body."""
import itertools, json, subprocess, threading, urllib.request

from src.mcp import protocol as p
from src.wire import log


class Client:
    def __init__(self, name, command=None, url=None):
        self.name, self.url = name, url
        self.ids = itertools.count(1)
        self.lock = threading.Lock()
        if command:
            self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            text=True, bufsize=1)

    def send(self, method, params=None):
        with self.lock:
            message = p.request(next(self.ids), method, params)
            if self.url:
                req = urllib.request.Request(self.url, json.dumps(message).encode(),
                                             {"Content-Type": "application/json",
                                              "MCP-Protocol-Version": p.VERSION})
                with urllib.request.urlopen(req, timeout=60) as r:
                    reply = json.load(r)
            else:
                self.process.stdin.write(json.dumps(message) + "\n")
                self.process.stdin.flush()
                reply = json.loads(self.process.stdout.readline())
        log("mcp", {"server": self.name, "request": message, "reply": reply})
        if "error" in reply:
            raise RuntimeError(f"{self.name}: {reply['error']['message']}")
        return reply["result"]

    def list_tools(self):
        return self.send("tools/list")["tools"]

    def call_tool(self, name, arguments):
        result = self.send("tools/call", {"name": name, "arguments": arguments})
        if "structuredContent" in result:
            return result["structuredContent"]
        return {"text": "".join(c.get("text", "") for c in result["content"])}

    def close(self):
        if not self.url:
            self.process.stdin.close()
            self.process.wait(timeout=5)
