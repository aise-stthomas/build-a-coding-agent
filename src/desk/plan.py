"""The plan: state the run writes with a tool, and the program places at the end of each request."""

UPDATE_PLAN = {
    "name": "update_plan",
    "description": "Replace the plan. steps: each step as one line starting with [done], [doing] or [to do].",
    "parameters": {"type": "object", "properties": {
        "steps": {"type": "array", "items": {"type": "string"}}}, "required": ["steps"]},
}


class Plan:
    def __init__(self, steps=None):
        self.steps = steps or []

    def update(self, steps):
        self.steps = steps
        return {"ok": True, "steps": len(steps)}

    def render(self, contents):
        """What is sent: the contents, with the plan as the last thing in the request."""
        if not self.steps:
            return contents
        note = {"text": "Current plan:\n" + "\n".join(self.steps)}
        last = contents[-1]
        if last["role"] == "user":
            return contents[:-1] + [{"role": "user", "parts": last["parts"] + [note]}]
        return contents + [{"role": "user", "parts": [note]}]
