from pathlib import Path
from branchsmith.engine import run_repair
from branchsmith.planner import DemoPlanner
from branchsmith.sandbox import LocalSandbox

repo = Path(__file__).resolve().parents[1] / "examples" / "buggy_calc"
report = run_repair(
    repo=repo,
    issue="add() subtracts instead of adding",
    test_command="python -m unittest -q",
    planner=DemoPlanner(),
    sandbox=LocalSandbox(),
    candidate_count=3,
)
print(report.to_dict())
raise SystemExit(0 if report.winner_id else 2)
