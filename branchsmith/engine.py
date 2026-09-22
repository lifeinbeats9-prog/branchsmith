from __future__ import annotations

from pathlib import Path

from .models import CandidateResult, RunReport
from .planner import Planner
from .sandbox import Sandbox


def collect_context(repo: Path, *, max_total_chars: int = 80_000) -> dict[str, str]:
    suffixes = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".md", ".toml", ".yaml", ".yml", ".json"}
    out: dict[str, str] = {}
    used = 0
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in suffixes:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if used + len(body) > max_total_chars:
            continue
        out[path.relative_to(repo).as_posix()] = body
        used += len(body)
    return out


def run_repair(*, repo: Path, issue: str, test_command: str, planner: Planner, sandbox: Sandbox, candidate_count: int = 3) -> RunReport:
    repo = repo.resolve()
    baseline = sandbox.baseline(repo, test_command)
    if baseline.passed:
        return RunReport(issue, baseline, (), None, planner.name, sandbox.name)
    baseline_output = (baseline.stdout + "\n" + baseline.stderr).strip()
    candidates = planner.plan(
        issue=issue,
        baseline_output=baseline_output,
        files=collect_context(repo),
        candidate_count=candidate_count,
    )
    results: list[CandidateResult] = []
    for candidate in candidates:
        test = sandbox.evaluate(repo, candidate, test_command)
        results.append(CandidateResult(candidate, test, len(candidate.edits)))
    passing = [x for x in results if x.test.passed]
    passing.sort(key=lambda x: (x.edit_count, x.candidate.candidate_id))
    winner = passing[0].candidate.candidate_id if passing else None
    return RunReport(issue, baseline, tuple(results), winner, planner.name, sandbox.name)
