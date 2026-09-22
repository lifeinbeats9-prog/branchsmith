# Devpost draft — BranchSmith v0.3

## One-line description

BranchSmith turns software repair into a controlled experiment: NVIDIA Nemotron proposes competing patches, isolated execution backends test each from the same source baseline, and only evidence-passing repairs can win.

## Primary track

Coding and Agentic Engineering, contingent on live Nebius ConTree access before submission.

Fallback track: Best Apps and Agents if Sandboxes beta access remains unavailable. The core product and Token Factory/Nemotron runtime do not change.

## What it does

Given a failing repository, an issue description, and a trusted test command, BranchSmith:

1. captures the baseline failure;
2. asks NVIDIA Nemotron for multiple small, distinct repair candidates;
3. evaluates each candidate independently;
4. runs the exact same test command for every candidate;
5. selects a passing candidate with the smallest edit count;
6. returns no winner when no candidate passes.

## Execution backends

BranchSmith automatically chooses the strongest available backend:

- Nebius Token Factory Sandboxes / ConTree — native checkpoints and candidate branches;
- Docker — no-network container with CPU and memory bounds;
- isolated local workspace — independent temporary copies, secret-like environment stripping and timeout enforcement.

This makes execution availability a backend choice rather than a product-wide blocker.

## Nebius + NVIDIA

- Nebius Token Factory: hosted inference API for the repair planner.
- NVIDIA model: `nvidia/nemotron-3-super-120b-a12b`.
- Nebius Sandboxes / ConTree: preferred coding-track execution backend when beta access is available.

The model routing key and API base URL used by BranchSmith match the official Token Factory Playground code surface.

## Current evidence

- Live Token Factory Playground inference with Nemotron 3 Super: PASS.
- BranchSmith-owned hosted Token Factory/Nemotron runtime: PASS.
- Hosted `/api/demo`: HTTP 200 with a real winner selected after unchanged tests.
- Hosted demo URL: https://branchsmith-demo.onrender.com
- BranchSmith v0.3 local tests: 15/15 PASS.
- Compile validation: PASS.
- Evidence-dashboard smoke test: PASS.
- Public GitHub Actions: PASS on Python 3.10, 3.11 and 3.12.
- Governance/private-system leak scan before publication: PASS.
- Secret-material scan before publication: PASS.
- Live ConTree branch/test evidence: pending Sandboxes beta approval.

## Public repository

https://github.com/lifeinbeats9-prog/branchsmith

Release: `v0.3.0`.

The repository is MIT-licensed and contains the product source, tests, fixture, web demo surface, setup instructions and submission documentation.

## Why it is different

Branching is a decision primitive rather than a source-control convenience. Candidate patches are competing hypotheses. They start from the same source baseline and face the same tests, so the agent exposes both successful and failed alternatives instead of collapsing immediately to one model answer.

The evidence rule is simple: no passing test, no winner.

## Hosted demo

The hosted demo uses only the bundled public `buggy_calc` fixture. It does not execute user-supplied code or commands. The Token Factory API key remains server-side.

Demo URL: https://branchsmith-demo.onrender.com

## Sponsor feedback notes to finalize after the ConTree access decision

- Token Factory model quality and response-shape reliability.
- ConTree onboarding and beta-access friction.
- Value of native checkpoint/branch semantics for competing repair hypotheses.
- Fallback behavior when Sandboxes access is unavailable.
