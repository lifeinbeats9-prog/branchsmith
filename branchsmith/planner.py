from __future__ import annotations

import json
import os
import re
from typing import Protocol

from .models import Candidate


class Planner(Protocol):
    name: str

    def plan(
        self,
        *,
        issue: str,
        baseline_output: str,
        files: dict[str, str],
        candidate_count: int,
    ) -> list[Candidate]: ...


def _extract_json(text: str) -> object:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = min([i for i in (stripped.find("{"), stripped.find("[")) if i >= 0], default=-1)
        if start < 0:
            raise
        for end in range(len(stripped), start, -1):
            try:
                return json.loads(stripped[start:end])
            except json.JSONDecodeError:
                continue
        raise


class NemotronPlanner:
    """Nebius Token Factory planner using NVIDIA Nemotron 3 Super."""

    name = "nebius-token-factory:nvidia/nemotron-3-super-120b-a12b"

    def __init__(self, *, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("NEBIUS_API_KEY")
        if not self.api_key:
            raise RuntimeError("NEBIUS_API_KEY is required for live planning")
        self.model = model or os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-super-120b-a12b")
        self.base_url = base_url or os.getenv(
            "NEBIUS_BASE_URL", "https://api.tokenfactory.us-central1.nebius.com/v1/"
        )

    def plan(self, *, issue: str, baseline_output: str, files: dict[str, str], candidate_count: int) -> list[Candidate]:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("install live dependencies: pip install '.[live]'") from exc

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        file_block = "\n\n".join(f"### {path}\n```\n{body}\n```" for path, body in files.items())
        schema = {
            "candidates": [
                {
                    "candidate_id": "short-id",
                    "rationale": "why this could fix the failure",
                    "edits": [{"path": "relative/path", "old": "exact old text", "new": "replacement text"}],
                }
            ]
        }
        prompt = f"""You are a software repair planner. Propose exactly {candidate_count} small, mutually distinct patches.
Return JSON only, matching this shape: {json.dumps(schema)}
Rules: only edit files shown below; every `old` must be an exact unique substring; minimize edits; do not weaken/delete tests.

ISSUE:\n{issue}\n\nBASELINE TEST OUTPUT:\n{baseline_output}\n\nFILES:\n{file_block}
"""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Generate precise, testable software repair candidates as strict JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=1.0,
            top_p=0.95,
        )
        content = response.choices[0].message.content or ""
        raw = _extract_json(content)
        if not isinstance(raw, dict) or not isinstance(raw.get("candidates"), list):
            raise RuntimeError("planner response did not contain candidates[]")
        return [Candidate.from_dict(x, i + 1) for i, x in enumerate(raw["candidates"][:candidate_count])]


class DemoPlanner:
    """Deterministic offline planner for the bundled smoke fixture only."""

    name = "offline-demo-fixture"

    def plan(self, *, issue: str, baseline_output: str, files: dict[str, str], candidate_count: int) -> list[Candidate]:
        options = [
            {
                "candidate_id": "swap-minus-to-plus",
                "rationale": "The add function subtracts instead of adding.",
                "edits": [{"path": "calc.py", "old": "return a - b", "new": "return a + b"}],
            },
            {
                "candidate_id": "wrong-zero-fix",
                "rationale": "Deliberately wrong competing branch used to prove branch evaluation.",
                "edits": [{"path": "calc.py", "old": "return a - b", "new": "return 0"}],
            },
            {
                "candidate_id": "wrong-multiply-fix",
                "rationale": "Another deliberately wrong competing branch.",
                "edits": [{"path": "calc.py", "old": "return a - b", "new": "return a * b"}],
            },
        ]
        return [Candidate.from_dict(x, i + 1) for i, x in enumerate(options[:candidate_count])]
