# BranchSmith submission readiness checklist

## Competition requirements

- [x] Product repository is public and MIT-licensed.
- [x] Product includes a runtime Nebius Token Factory inference path using NVIDIA Nemotron 3 Super.
- [x] Coding-agent execution backend is implemented with Nebius Token Factory Sandboxes / ConTree; Docker and local isolated workspaces are fallback backends.
- [x] Public hosted demo is constrained to the bundled `buggy_calc` fixture and does not accept user code or commands.
- [x] Current public demo deployment is live; read-only `/healthz` returned release `0.3.1` and `accepts_user_code=false` for merged commit `ab413e7`.
- [x] Public product test suite: 18/18 pass on local macOS outside the restricted sandbox; the merged dashboard change also passed the Python 3.10, 3.11 and 3.12 GitHub Actions matrix.
- [x] Judge-facing evidence view shows baseline and candidate test output and distinguishes API errors from completed no-winner experiments.
- [x] Development ConTree authentication and a scoped native branch/file-staging witness were captured. This is not a full hosted product acceptance result.
- [ ] Capture a fresh live hosted Nemotron repair run for the current deployment; this may use Token Factory credits.
- [ ] Upload a public YouTube demo under three minutes showing the application functioning.
- [ ] Complete Devpost enrollment and all required fields.
- [ ] Select the final track after confirming the submitted video demonstrates the corresponding runtime path.
- [ ] Complete sponsor/tool feedback based on firsthand product use.
- [ ] Confirm free, unrestricted judge access through the end of the judging period.
- [ ] Submit before 2026-10-30 10:00 AM Pacific Time (17:00 UTC).

## Public repository

https://github.com/lifeinbeats9-prog/branchsmith

Current release: `v0.3.1`.

## Evidence scope

The ConTree witness confirms authenticated development access and a scoped test of the native branching/staging path. It does not establish full product acceptance, hosted demo inference quality, or an end-to-end native run of the public product repository. The current deployment health check is read-only; no fresh paid inference run was performed during this update.

## Optional surfaces

- Tavily bonus is not claimed; no functional Tavily runtime call is part of the project.
- City Winner eligibility is not claimed without qualifying in-person attendance evidence.
