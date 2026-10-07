# Devpost draft — BranchSmith v0.3.1

## One-line description

BranchSmith turns software repair into a controlled experiment: NVIDIA Nemotron proposes competing patches, independent workspaces test each from the same source baseline, and only evidence-passing repairs can win.

## Recommended track

Coding and Agentic Engineering, provided the final demo clearly shows the coding agent writing, running, and testing code through the Nebius Token Factory Sandbox / ConTree path. The public CLI implements this native backend and prefers it when authenticated access is available, with Docker and isolated local workspaces as fallbacks.

The hosted web demo uses a fixed public fixture and a local isolated sandbox. It demonstrates the repair workflow and hosted Token Factory planner, but does not by itself demonstrate native ConTree branch execution. If the final video cannot show the native path, reassess track fit before selecting a track in Devpost.

## What it does

Given a failing repository, an issue description, and a trusted test command, BranchSmith:

1. captures the baseline failure;
2. asks NVIDIA Nemotron for multiple small repair candidates;
3. evaluates each candidate independently from the same source baseline;
4. runs the exact same test command for every candidate;
5. ranks passing candidates by fewest edits, then smallest replaced source span, with candidate ID as the final deterministic tie-break;
6. returns no winner when no candidate passes.

The dashboard presents the baseline and candidate outputs, passing/failing status, proposed edits, and raw JSON evidence. The public hosted demo is deliberately restricted to the bundled `buggy_calc` fixture; it never executes user-supplied code or commands.

## Nebius + NVIDIA

- Nebius Token Factory: runtime inference for the repair planner.
- NVIDIA model: `nvidia/nemotron-3-super-120b-a12b`.
- Nebius Token Factory Sandboxes / ConTree: native execution backend implemented in the public CLI; Docker and isolated local workspaces provide fallbacks.

## Current evidence (2026-10-07)

- Public repository: https://github.com/lifeinbeats9-prog/branchsmith (MIT licensed).
- Public demo: https://branchsmith-demo.onrender.com
- Render deployment for merged commit `ab413e7de2e2b7ed746d9d081e401dd0f326209b`: live.
- Read-only hosted `/healthz`: `status=ok`, version `0.3.1`, bundled fixture, and `accepts_user_code=false`.
- Product tests: 18/18 passed on local macOS outside the restricted sandbox; GitHub Actions passed for Python 3.10, 3.11 and 3.12 on the merged dashboard change.
- Existing ConTree profile authentication and a scoped native development witness passed. The witness covers independent baseline/candidate branches, identical staging of two r2 regression modules, and 22/22 candidate tests. It does not prove full hosted product acceptance or current hosted model inference.
- No fresh hosted inference was run for this draft.

## Demo URL

https://branchsmith-demo.onrender.com

## Video and remaining submission fields

Publish a sub-three-minute video on YouTube showing a baseline failure, independent candidate results, and the evidence-bound winner. Include a native ConTree coding path if selecting Coding and Agentic Engineering. Paste the public YouTube URL into the Devpost form.

Complete Nebius/NVIDIA feedback after firsthand runtime use. Confirm the demo remains free and unrestricted for judging through 2026-12-15 12:00 PM Pacific Time.

## Submission status

This is a draft only. Devpost enrollment is not complete and no final submission has been made.
