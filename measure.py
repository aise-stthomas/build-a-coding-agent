"""What declarations and edits cost, in input tokens, counted by the provider.

  uv run measure.py     prints a table; writes data/wire/measure.json
"""
import json, os

from dotenv import load_dotenv
load_dotenv()

from src.agent.messages import user_message
from src.agent.model import Model
from src.agent.toolbox import connect, for_model

model = Model()
base_contents = [user_message("x")]
base = model.count_tokens("x", base_contents)
out = {"base": base, "tools": {}, "servers": {}}

clients = connect()
every = []
for name, c in clients.items():
    decls = [for_model(d) for d in c.tools]
    every += decls
    out["servers"][name] = model.count_tokens("x", base_contents, decls) - base
    for d in decls:
        out["tools"][d["name"]] = model.count_tokens("x", base_contents, [d]) - base
out["all_tools"] = model.count_tokens("x", base_contents, every) - base
out["n_tools"] = len(every)
allowed = [for_model(d) for c in clients.values() for d in c.tools if d["name"] in c.allow]
out["allowed_tools"] = model.count_tokens("x", base_contents, allowed) - base
out["n_allowed"] = len(allowed)

# Rewriting a file versus replacing one string in it.
cart = open(os.path.join("data", "sample-repo", "src", "checkout", "cart.py")).read()
old, new = "return subtotal(items) * TAX_RATE", "return int(subtotal(items) * TAX_RATE + 0.5)"
rewrite = cart.replace(old, new)
out["edit"] = {
    "file_lines": cart.count("\n"),
    "rewrite_tokens": model.count_tokens("x", [user_message(rewrite)]) - model.count_tokens("x", [user_message("")]),
    "replace_tokens": model.count_tokens("x", [user_message(old + "\n" + new)]) - model.count_tokens("x", [user_message("")]),
}

for k, v in out["tools"].items():
    print(f"  {k:<24} {v:>4} tokens")
print(f"  all {out['n_tools']} tools: {out['all_tools']}   allowed {out['n_allowed']}: {out['allowed_tools']}")
print("  per server:", out["servers"])
print("  edit:", out["edit"])
os.makedirs("data/wire", exist_ok=True)
json.dump(out, open("data/wire/measure.json", "w"), indent=1)
