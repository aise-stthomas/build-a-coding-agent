"""Start over: empty the payments refunds, the runs, the cut results, and the coding agent's
workspace (a fresh copy of data/sample-repo, whose tests fail).

  uv run reset.py            the failing repository, for Mains 9 and 10
  uv run reset.py --fixed    the same repository with the bug fixed, for Main 11
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(ROOT, "data", "state")
WORKSPACE = os.path.join(ROOT, "workspace")

if os.path.isdir(STATE):
    shutil.rmtree(STATE)
os.makedirs(STATE)
if os.path.isdir(WORKSPACE):
    shutil.rmtree(WORKSPACE)
shutil.copytree(os.path.join(ROOT, "data", "sample-repo"), WORKSPACE,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
if "--fixed" in sys.argv:
    cart = os.path.join(WORKSPACE, "src", "checkout", "cart.py")
    text = open(cart).read().replace("return subtotal(items) * TAX_RATE", "return int(subtotal(items) * TAX_RATE + 0.5)")
    open(cart, "w").write(text)
for cmd in (["git", "init", "-q"], ["git", "add", "."],
            ["git", "-c", "user.name=lab", "-c", "user.email=lab@example.com", "commit", "-q", "-m", "start"]):
    subprocess.run(cmd, cwd=WORKSPACE, check=True)
print("reset: data/state/ emptied; workspace/ is a fresh copy of data/sample-repo/" + (", with the bug fixed" if "--fixed" in sys.argv else ""))
