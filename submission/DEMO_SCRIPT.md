# Demo script — target 2:20–2:40

## 0:00–0:20 — Problem
Show a real repository with a reproducible failing test. Explain that single-shot code agents can hide uncertainty by committing one untested answer.

## 0:20–0:45 — Plan
Run BranchSmith. Show NVIDIA Nemotron on Nebius Token Factory proposing several small, distinct repair candidates.

## 0:45–1:35 — Native branch evaluation
Show one Nebius Sandboxes / ConTree baseline session, then separate candidate branches created from the same baseline checkpoint. Run the identical test command on each branch.

## 1:35–2:05 — Evidence-based selection
Show failed alternatives beside the passing candidate. BranchSmith selects the passing candidate with the smallest edit count; if none pass, it returns no winner.

## 2:05–2:30 — Why the stack matters
Show that Token Factory supplies the NVIDIA planner and Sandboxes provide isolated branch/rollback execution. Emphasize that branching is part of the product behavior, not a demo convenience.

## 2:30–2:40 — Close
Show the public repository, MIT license, and reproducible run command.

Keep the final uploaded video under the official three-minute limit.
