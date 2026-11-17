"""Start over: workspace/ becomes a fresh copy of data/sample-repo, a repository whose tests fail.

  uv run reset.py            the broken repository, for Mains 1 and 2
  uv run reset.py --fixed    the same repository with the bug fixed, for Main 3

The workspace is a git repository whose origin is a folder on this laptop, so a push goes
nowhere public. See what reached it with: git -C workspace ls-remote origin
"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(ROOT, "workspace")

if os.path.isdir(WORKSPACE):
    shutil.rmtree(WORKSPACE)
shutil.copytree(os.path.join(ROOT, "data", "sample-repo"), WORKSPACE,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
if "--fixed" in sys.argv:
    cart = os.path.join(WORKSPACE, "src", "checkout", "cart.py")
    text = open(cart).read().replace("return subtotal(items) * TAX_RATE", "return int(subtotal(items) * TAX_RATE + 0.5)")
    open(cart, "w").write(text)
ORIGIN = os.path.join(ROOT, "data", "state", "origin.git")    # stands in for a remote: pushes land here
if os.path.isdir(ORIGIN):
    shutil.rmtree(ORIGIN)
os.makedirs(os.path.dirname(ORIGIN), exist_ok=True)
subprocess.run(["git", "init", "-q", "--bare", ORIGIN], check=True)
for cmd in (["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.name", "lab"], ["git", "config", "user.email", "lab@example.com"],
            ["git", "remote", "add", "origin", ORIGIN],
            ["git", "add", "."], ["git", "commit", "-q", "-m", "start"], ["git", "push", "-q", "origin", "main"]):
    subprocess.run(cmd, cwd=WORKSPACE, check=True)
with open(os.path.join(WORKSPACE, ".git", "info", "exclude"), "a") as f:
    f.write("__pycache__/\n.pytest_cache/\n")
print("reset: workspace/ is a fresh copy of data/sample-repo/" + (", with the bug fixed" if "--fixed" in sys.argv else "")
      + ". Its origin is data/state/origin.git, on this laptop.")
