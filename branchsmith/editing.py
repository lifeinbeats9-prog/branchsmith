from __future__ import annotations

from pathlib import Path

from .models import Candidate


class EditError(RuntimeError):
    pass


def safe_target(root: Path, relative: str) -> Path:
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise EditError(f"edit escapes repository root: {relative}")
    return target


def _looks_like_test(relative: str) -> bool:
    p = Path(relative)
    lower_parts = [x.lower() for x in p.parts]
    name = p.name.lower()
    return (
        "tests" in lower_parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.js")
        or name.endswith(".test.ts")
        or name.endswith(".spec.js")
        or name.endswith(".spec.ts")
    )


def apply_candidate(root: Path, candidate: Candidate) -> list[Path]:
    changed: list[Path] = []
    for edit in candidate.edits:
        if _looks_like_test(edit.path):
            raise EditError(f"candidate edits protected test file: {edit.path}")
        target = safe_target(root, edit.path)
        if not target.is_file():
            raise EditError(f"edit target does not exist: {edit.path}")
        text = target.read_text(encoding="utf-8")
        occurrences = text.count(edit.old)
        if occurrences != 1:
            raise EditError(
                f"expected exactly one occurrence in {edit.path}; found {occurrences}"
            )
        target.write_text(text.replace(edit.old, edit.new, 1), encoding="utf-8")
        changed.append(target)
    return changed
