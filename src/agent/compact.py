"""Keeping each request inside a budget.

Two tools for it. A long tool result is cut, and the whole of it kept in a file the next call
can name. When a request would still pass the budget, the oldest turns are replaced, in what is
sent, by a summary one model call writes. The full contents are kept unchanged."""
import json, os

from src.agent.messages import text_in, model_turn, user_message

KEEP = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "state", "results")

SUMMARIZE = """Summarize the work so far for the agent that will continue it. Keep every id,
amount, time and tool result that a later step may need, word for word. Say what was found
and what is still open. At most twelve lines."""


def cut(name, result, limit=4000):
    """A result longer than the limit is cut; the full result goes to a file."""
    text = json.dumps(result)
    if len(text) <= limit:
        return result
    os.makedirs(KEEP, exist_ok=True)
    path = os.path.join(KEEP, f"{name}-{abs(hash(text)) % 10**6}.json")
    open(path, "w").write(text)
    return {"cut": f"first {limit} of {len(text)} characters. The full result is in {os.path.relpath(path)}",
            "start": text[:limit]}


def estimate(contents):
    return len(json.dumps(contents)) // 4      # about four characters to a token


class Compactor:
    def __init__(self, model, budget, trace=None):
        self.model, self.budget, self.trace = model, budget, trace
        self.summary, self.upto = None, 1      # contents[1:upto] are covered by the summary

    def sent(self, contents):
        if self.summary is None:
            return contents
        note = user_message("Summary of the earlier turns:\n" + self.summary)
        return [contents[0], note] + contents[self.upto:]

    def size(self, out, contents):
        """The last request's measured size, plus an estimate of what was added since."""
        measured = [t["prompt_tokens"] for t in self.trace.turns if t["agent"] == "lead"] if self.trace else []
        return measured[-1] + estimate(contents[-2:]) if measured else estimate(out)

    def __call__(self, contents):
        out = self.sent(contents)
        if self.size(out, contents) > self.budget and len(contents) - self.upto > 2:
            # Summarize everything but the newest call and its results.
            self.upto = len(contents) - 2
            covered = self.sent(contents[:self.upto]) if self.summary else contents[:self.upto]
            response = self.model.generate(SUMMARIZE, covered + [user_message("Write the summary now.")])
            self.summary = text_in(model_turn(response))
            if self.trace:
                self.trace.record("compaction", len(contents) // 2, response, [], [])
            out = self.sent(contents)
        return out
