# Devpost draft — BranchSmith

## One-line description
BranchSmith turns software repair into a controlled experiment: NVIDIA Nemotron proposes competing patches, Nebius Sandboxes test each from the same baseline branch, and only evidence-passing repairs can win.

## Track
Coding and Agentic Engineering.

## What it does
Given a failing repository, an issue description, and a test command, BranchSmith captures the baseline failure, asks NVIDIA Nemotron for multiple minimal repair candidates, executes each candidate independently on a Nebius Token Factory Sandbox branch, and reports the best passing candidate. If none pass, it reports no winner rather than inventing success.

## Nebius + NVIDIA
- Nebius Token Factory: hosted inference API for the repair planner.
- NVIDIA model: `nvidia/nemotron-3-super-120b-a12b`.
- Nebius Token Factory Sandboxes / ConTree: isolated execution, checkpoints, candidate branching, test runs, and rollback.

## Why it is different
Branching is a decision primitive. Candidate patches share one known baseline and are compared under the same test command, so the agent exposes competing hypotheses and their execution evidence instead of collapsing immediately to one model answer.

## Open source
The submission product is MIT-licensed. The public submission repository contains the source, setup instructions, tests, and demo commands required to reproduce BranchSmith; no unrelated private system is required.

## Current evidence
Offline deterministic QA verifies the engine's branching/selection contract and safety guards. A live Nebius/Nemotron witness is the next release gate before external submission.
