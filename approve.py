"""A person decides on a waiting run, and the run resumes.

  uv run approve.py <run_id>                 approve, as "a reviewer"
  uv run approve.py <run_id> --decline
  uv run approve.py <run_id> --by "J. Howard"
"""
import argparse

from src.agent.runs import Runs
from resume import resume

ap = argparse.ArgumentParser()
ap.add_argument("run_id")
ap.add_argument("--decline", action="store_true")
ap.add_argument("--by", default="a reviewer")
args = ap.parse_args()

runs = Runs()
row = runs.load(args.run_id)
if row["status"] != "waiting":
    print(f"{args.run_id} is {row['status']}, not waiting; nothing to decide.")
else:
    runs.decide(args.run_id, args.by, "declined" if args.decline else "approved")
    resume(args.run_id)
