# BranchSmith

BranchSmith is an evidence-driven software repair agent built for the Nebius × NVIDIA Global AI Hackathon.

Instead of asking one model for one patch, BranchSmith asks NVIDIA Nemotron for several small repair candidates, evaluates every candidate in an independent execution workspace from the same source baseline, runs the same test command, and selects a winner only when test evidence passes.

## Architecture

1. Run the repository's test command to capture a failing baseline.
2. Send the issue, baseline output, and bounded repository context to `nvidia/nemotron-3-super-120b-a12b` through Nebius Token Factory.
3. Parse multiple precise candidate edits.
4. Evaluate each candidate independently using one of three execution backends.
5. Run the exact same test command for every candidate.
6. Rank passing candidates by fewest edits, then smallest replaced source span, then candidate ID; return no winner when none pass.

## Execution backends

`--sandbox auto` chooses the strongest available backend in this order:

1. **Nebius ConTree** — native Token Factory Sandbox checkpoints and branches.
2. **Docker** — isolated container, network disabled, CPU/memory bounded.
3. **Local isolated workspace** — independent temporary copy, secret-like environment variables stripped, timeout enforced; on macOS, network is denied with `sandbox-exec` by default.

The planner and execution backend are separate interfaces. The same repair engine therefore keeps working if a particular execution service is unavailable.

## Offline smoke test

~~~bash
git clone https://github.com/lifeinbeats9-prog/branchsmith.git
cd branchsmith
PYTHONPATH=. python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 scripts/offline_demo.py
~~~

The bundled fixture starts with a broken `add()` implementation. Three competing repairs are evaluated independently and only the unchanged-test winner is selected.

## Live Token Factory + automatic backend

Requirements:

- Python 3.10+
- Nebius Token Factory API key
- `pip install -e '.[live]'`
- Optional: authenticated ConTree access
- Optional: Docker

~~~bash
export NEBIUS_API_KEY='...'

branchsmith /path/to/repo \
  --issue "Describe the failing behavior" \
  --test "python3 -m unittest -q" \
  --candidates 3 \
  --sandbox auto
~~~

When ConTree access is available, authenticate it separately:

~~~bash
contree auth
contree auth list
~~~

Then `--sandbox auto` will prefer ConTree. If it is unavailable, BranchSmith falls back without changing the repair workflow.

## Explicit backend selection

~~~bash
branchsmith ./repo --issue "..." --test "pytest -q" --sandbox contree
branchsmith ./repo --issue "..." --test "pytest -q" --sandbox docker
branchsmith ./repo --issue "..." --test "pytest -q" --sandbox local
~~~

Useful controls:

- `--timeout 120` — fail a test run closed after the deadline.
- `--docker-image python:3.11-slim` — choose the Docker test image.
- `--allow-network` — opt in to network access for the local fallback.

## Safety properties

- Candidate paths are confined to the target repository.
- Candidate edits must match exactly one source substring.
- Candidate patches may not edit detected test files.
- Baseline and candidates use independent temporary workspaces in fallback mode.
- Secret-like host environment variables are removed from fallback test processes.
- Common credential files and environment files are excluded from workspace copies/uploads.
- Docker fallback disables network access and bounds CPU/memory.
- Local fallback enforces a timeout and denies network on macOS unless explicitly overridden.
- A candidate is never called a winner without a passing test exit code.
- Offline demo output is clearly labeled and is not represented as live sponsor-stack evidence.

## Hackathon track strategy

Primary target: **Coding and Agentic Engineering** when live ConTree access is available.

Fallback: **Best Apps and Agents** if ConTree access is unavailable at submission time. The core product and Token Factory/Nemotron runtime remain the same; only the execution backend and track selection change.

## Hosted demo

Live demo: https://branchsmith-demo.onrender.com

The hosted surface is deliberately constrained to the bundled public `buggy_calc` fixture, so it never executes user-supplied repositories or commands.

The v0.3 evidence dashboard presents:

- the intentionally failing source baseline;
- the live NVIDIA Nemotron / Nebius Token Factory planner;
- each candidate patch as a separate evidence card;
- unchanged-test exit status for every candidate;
- the selected winner, backend, runtime, cache state and release;
- expandable raw JSON for reproducibility.

~~~bash
pip install -e '.[web]'
export NEBIUS_API_KEY='...'
gunicorn --bind 0.0.0.0:${PORT:-8000} branchsmith.web:app
~~~

Endpoints:

- `/` — interactive evidence dashboard.
- `/healthz` — no-secret health and release metadata.
- `/api/demo` — fixed-fixture live Nemotron repair experiment with a short result cache and single-run lock.

The Token Factory API key stays server-side.

## Open source

BranchSmith is MIT-licensed. The repository is self-contained and does not require unrelated private systems at runtime.
