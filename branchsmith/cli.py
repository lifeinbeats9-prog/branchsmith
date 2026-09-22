from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import run_repair
from .planner import DemoPlanner, NemotronPlanner
from .sandbox import LocalSandbox, select_sandbox


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="branchsmith",
        description="Plan competing repairs with NVIDIA Nemotron, test them independently, and select only evidence-passing patches.",
    )
    p.add_argument("repo", type=Path)
    p.add_argument("--issue", required=True)
    p.add_argument("--test", required=True, dest="test_command")
    p.add_argument("--candidates", type=int, default=3)
    p.add_argument(
        "--sandbox",
        choices=("auto", "contree", "docker", "local"),
        default="auto",
        help="Execution backend. auto prefers ConTree, then Docker, then isolated local workspaces.",
    )
    p.add_argument("--session", default=None, help="Pinned ConTree session name")
    p.add_argument("--timeout", type=int, default=120, help="Per-test timeout in seconds")
    p.add_argument("--docker-image", default="python:3.11-slim")
    p.add_argument(
        "--allow-network",
        action="store_true",
        help="Allow network access in local fallback. By default macOS local fallback denies network with sandbox-exec.",
    )
    p.add_argument(
        "--offline-demo",
        action="store_true",
        help="Use deterministic fixture planning and isolated local workspaces; never counts as live sponsor-stack evidence.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.offline_demo:
        planner = DemoPlanner()
        sandbox = LocalSandbox(timeout_seconds=args.timeout, deny_network=not args.allow_network)
    else:
        planner = NemotronPlanner()
        sandbox = select_sandbox(
            args.sandbox,
            session=args.session,
            timeout_seconds=args.timeout,
            docker_image=args.docker_image,
            allow_network=args.allow_network,
        )
    report = run_repair(
        repo=args.repo,
        issue=args.issue,
        test_command=args.test_command,
        planner=planner,
        sandbox=sandbox,
        candidate_count=args.candidates,
    )
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.winner_id else 2


if __name__ == "__main__":
    raise SystemExit(main())
