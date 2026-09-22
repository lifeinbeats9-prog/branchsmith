# BranchSmith demo script — target 2:20–2:45

## 0:00–0:18 — Problem

Show the broken `buggy_calc` fixture and its failing tests.

Narration: software-repair agents usually collapse uncertainty into one patch. BranchSmith treats repair candidates as competing hypotheses.

## 0:18–0:42 — Live model

Open the hosted BranchSmith demo and run the fixed public repair experiment.

Show that the planner is NVIDIA Nemotron 3 Super through Nebius Token Factory.

## 0:42–1:25 — Competing repairs

Show the JSON report containing multiple candidate edits.

Point out that every candidate starts from the same source baseline and is tested independently with the same unchanged test command.

If ConTree beta access is active by recording time, show the native ConTree branches/checkpoints here. Otherwise show the isolated fallback backend and state that the product automatically upgrades to ConTree when available.

## 1:25–1:55 — Evidence-bound winner

Show failed alternatives beside the passing repair.

Highlight:

- baseline fails;
- one or more candidate branches fail;
- only a candidate with test exit code 0 may become `winner_id`;
- no passing test means no winner.

## 1:55–2:18 — Resilience

Show the backend selection:

`ConTree -> Docker -> isolated local workspace`.

Explain that Sandboxes availability changes the execution backend, not the repair engine.

## 2:18–2:35 — Reproducibility

Show the public GitHub repository, MIT license, `v0.2.0` release, and green CI across Python 3.10/3.11/3.12.

## 2:35–2:45 — Close

Show the one-line thesis:

> Multiple repair hypotheses. Same baseline. Same tests. Evidence decides.

Keep the final uploaded video below the official three-minute limit.
