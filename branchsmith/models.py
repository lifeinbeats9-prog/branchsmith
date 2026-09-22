from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Edit:
    path: str
    old: str
    new: str

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Edit":
        return cls(path=str(raw["path"]), old=str(raw["old"]), new=str(raw["new"]))


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    rationale: str
    edits: tuple[Edit, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any], index: int) -> "Candidate":
        return cls(
            candidate_id=str(raw.get("candidate_id") or f"candidate-{index}"),
            rationale=str(raw.get("rationale") or ""),
            edits=tuple(Edit.from_dict(x) for x in raw.get("edits", [])),
        )


@dataclass(frozen=True)
class TestResult:
    exit_code: int
    stdout: str
    stderr: str
    branch: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True)
class CandidateResult:
    candidate: Candidate
    test: TestResult
    edit_count: int
    edit_span_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": asdict(self.candidate),
            "test": asdict(self.test),
            "passed": self.test.passed,
            "edit_count": self.edit_count,
            "edit_span_chars": self.edit_span_chars,
        }


@dataclass(frozen=True)
class RunReport:
    issue: str
    baseline: TestResult
    candidates: tuple[CandidateResult, ...]
    winner_id: str | None
    planner: str
    sandbox: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue": self.issue,
            "baseline": {**asdict(self.baseline), "passed": self.baseline.passed},
            "candidates": [x.to_dict() for x in self.candidates],
            "winner_id": self.winner_id,
            "planner": self.planner,
            "sandbox": self.sandbox,
        }
