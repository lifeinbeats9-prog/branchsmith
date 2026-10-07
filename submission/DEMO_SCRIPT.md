# BranchSmith demo script — target 2:30

## 0:00–0:20 — The problem

Show the bundled `buggy_calc` source returning subtraction and its failing baseline test.

Narration: “One generated patch hides uncertainty. BranchSmith treats repair candidates as competing hypotheses.”

## 0:20–0:40 — Nebius and NVIDIA

Show BranchSmith's Token Factory planner configuration and NVIDIA Nemotron 3 Super model identifier. Keep credentials and private account details off-screen.

## 0:40–1:20 — Independent candidates

Run one live, authorized experiment. Show the baseline failure, each candidate patch, and each unchanged-test result. Explain that the public hosted dashboard uses only the fixed `buggy_calc` fixture and a local isolated test sandbox.

## 1:20–1:55 — Native coding path

Show the CLI selecting Nebius Token Factory Sandboxes / ConTree, the baseline checkpoint, an independent candidate branch, identical test command, staged files, and the result. Capture a sanitized public-product run; do not show private repository names, private paths, or credentials.

If a fresh public-product native run is not available, label this section as a development witness and state its scope. Do not imply that a private regression test proves full product acceptance.

## 1:55–2:20 — Evidence-bound winner

Show the winner card and policy: tests must pass; passing candidates are ranked by edit count, replaced source span, and candidate ID; no passing candidate means no winner.

## 2:20–2:30 — Reproducibility

Show the public GitHub repository, MIT license, setup instructions, and close with:

> Multiple repair hypotheses. Same baseline. Same tests. Evidence decides.

Keep the final video below three minutes. Upload it publicly to YouTube and avoid unlicensed music or other third-party material.
