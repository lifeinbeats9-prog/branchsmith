from __future__ import annotations

import html
import os
import shlex
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify

from . import __version__
from .engine import run_repair
from .planner import NemotronPlanner
from .sandbox import LocalSandbox

app = Flask(__name__)

_MODEL = "nvidia/nemotron-3-super-120b-a12b"
_PUBLIC_REPO = "https://github.com/lifeinbeats9-prog/branchsmith"
_FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "buggy_calc"
_ISSUE = "add() subtracts instead of adding"
_LOCK = threading.Lock()
_TEST_COMMAND = f"{shlex.quote(sys.executable)} -m unittest -q"
_CACHE_TTL_SECONDS = 60
_cached_at = 0.0
_cached_payload: dict | None = None

_INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>BranchSmith — Evidence-driven repair</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #090b10;
      --panel: #11151c;
      --panel2: #171c25;
      --line: #2a3240;
      --text: #f3f5f7;
      --muted: #9aa6b5;
      --good: #74e6a6;
      --bad: #ff8d8d;
      --accent: #9db7ff;
      --warn: #ffd580;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at 20% -10%, #1b2840 0, transparent 35%), var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }
    main { max-width: 1120px; margin: 0 auto; padding: 52px 22px 80px; }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .hero { display: grid; gap: 14px; margin-bottom: 30px; }
    .eyebrow { color: var(--accent); font-size: 13px; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    h1 { margin: 0; font-size: clamp(38px, 7vw, 72px); letter-spacing: -.045em; line-height: .95; }
    .thesis { max-width: 780px; margin: 0; color: #d4dae2; font-size: 19px; }
    .badges { display: flex; flex-wrap: wrap; gap: 8px; }
    .badge {
      border: 1px solid var(--line);
      background: #0e1218;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      color: #ccd4df;
    }
    .badge.good { border-color: #285e42; color: var(--good); }
    .layout { display: grid; grid-template-columns: 1.05fr .95fr; gap: 18px; }
    .panel {
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(23,28,37,.94), rgba(14,18,24,.96));
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 16px 50px rgba(0,0,0,.18);
    }
    .panel h2 { margin: 0 0 14px; font-size: 16px; letter-spacing: .01em; }
    .meta { color: var(--muted); font-size: 13px; }
    pre, code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; }
    .code {
      margin: 12px 0 0;
      padding: 14px;
      background: #080a0e;
      border: 1px solid #222a35;
      border-radius: 10px;
      color: #dbe4ef;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .action-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 18px; }
    button {
      border: 0;
      border-radius: 10px;
      padding: 12px 16px;
      font: inherit;
      font-weight: 750;
      background: #edf2ff;
      color: #101521;
      cursor: pointer;
    }
    button:disabled { cursor: wait; opacity: .55; }
    .state { font-size: 13px; color: var(--muted); }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0,1fr));
      gap: 10px;
      margin: 18px 0;
    }
    .metric {
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 11px;
      background: #0c1016;
    }
    .metric .label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; }
    .metric .value { margin-top: 4px; font-size: 15px; font-weight: 750; overflow-wrap: anywhere; }
    .candidate-grid { display: grid; gap: 12px; }
    .candidate {
      border: 1px solid var(--line);
      background: var(--panel2);
      border-radius: 13px;
      padding: 15px;
    }
    .candidate.winner { border-color: #3b8f63; box-shadow: inset 0 0 0 1px rgba(116,230,166,.16); }
    .candidate-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
    .candidate-id { font-weight: 800; }
    .pill { border-radius: 999px; padding: 4px 8px; font-size: 11px; font-weight: 800; }
    .pill.pass { color: var(--good); background: rgba(116,230,166,.09); }
    .pill.fail { color: var(--bad); background: rgba(255,141,141,.09); }
    .pill.win { color: #0b1811; background: var(--good); margin-left: 6px; }
    .rationale { margin: 9px 0; color: #c3ccd7; font-size: 13px; }
    .edit { background: #0a0d12; border-radius: 9px; padding: 10px; margin-top: 8px; font-size: 12px; }
    .old { color: var(--bad); }
    .new { color: var(--good); }
    .empty { color: var(--muted); padding: 20px 0; }
    details { margin-top: 16px; border-top: 1px solid var(--line); padding-top: 14px; }
    summary { cursor: pointer; color: var(--muted); font-size: 13px; }
    #raw { max-height: 420px; overflow: auto; font-size: 11px; }
    .rule { border-left: 3px solid var(--accent); padding: 10px 12px; background: rgba(157,183,255,.06); border-radius: 7px; color: #d8e0ed; }
    footer { margin-top: 22px; color: var(--muted); font-size: 12px; display: flex; gap: 14px; flex-wrap: wrap; }
    @media (max-width: 800px) {
      .layout { grid-template-columns: 1fr; }
      .summary { grid-template-columns: repeat(2, minmax(0,1fr)); }
    }
  </style>
</head>
<body>
<main>
  <section class="hero">
    <div class="eyebrow">Nebius × NVIDIA · live repair experiment</div>
    <h1>BranchSmith</h1>
    <p class="thesis">Multiple repair hypotheses. Same baseline. Same tests. Evidence decides.</p>
    <div class="badges">
      <span class="badge good">LIVE DEMO</span>
      <span class="badge">NVIDIA Nemotron 3 Super</span>
      <span class="badge">Nebius Token Factory</span>
      <span class="badge">v__VERSION__</span>
    </div>
  </section>

  <section class="layout">
    <div class="panel">
      <h2>01 · Controlled experiment</h2>
      <div class="meta">The hosted demo is deliberately fixed. It never executes user-supplied repositories or commands.</div>
      <p><strong>Issue</strong><br>add() subtracts instead of adding</p>
      <div class="code">__SOURCE__</div>
      <div class="action-row">
        <button id="run">Run live repair experiment</button>
        <span class="state" id="state">Ready.</span>
      </div>
      <div class="rule" style="margin-top:18px"><strong>Evidence rule:</strong> a candidate can only win after the unchanged test command exits 0.</div>
    </div>

    <div class="panel">
      <h2>02 · Evidence summary</h2>
      <div id="summary" class="empty">Run the experiment to generate live evidence.</div>
      <div id="metrics" class="summary" style="display:none"></div>
    </div>
  </section>

  <section class="panel" style="margin-top:18px">
    <h2>03 · Competing candidates</h2>
    <div id="candidates" class="empty">No candidates yet.</div>
    <details>
      <summary>Raw evidence JSON</summary>
      <pre id="raw" class="code">No run yet.</pre>
    </details>
  </section>

  <footer>
    <span>Public source: <a href="__REPO__" target="_blank" rel="noreferrer">GitHub</a></span>
    <span>Release: <a href="__REPO__/releases/tag/v__VERSION__" target="_blank" rel="noreferrer">v__VERSION__</a></span>
    <span>Hosted execution: fixed public fixture only</span>
  </footer>
</main>

<script>
  const runButton = document.getElementById("run");
  const stateEl = document.getElementById("state");
  const summaryEl = document.getElementById("summary");
  const metricsEl = document.getElementById("metrics");
  const candidatesEl = document.getElementById("candidates");
  const rawEl = document.getElementById("raw");

  function esc(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function metric(label, value) {
    return '<div class="metric"><div class="label">' + esc(label) + '</div><div class="value">' + esc(value) + '</div></div>';
  }

  function renderCandidate(item, winnerId) {
    const c = item.candidate || {};
    const t = item.test || {};
    const isWinner = c.candidate_id === winnerId;
    const status = item.passed ? '<span class="pill pass">PASS</span>' : '<span class="pill fail">FAIL</span>';
    const win = isWinner ? '<span class="pill win">WINNER</span>' : '';
    const edits = (c.edits || []).map(function(edit) {
      return '<div class="edit"><strong>' + esc(edit.path) + '</strong>' +
        '<div class="old">− ' + esc(edit.old) + '</div>' +
        '<div class="new">+ ' + esc(edit.new) + '</div></div>';
    }).join("");
    return '<article class="candidate' + (isWinner ? ' winner' : '') + '">' +
      '<div class="candidate-head"><span class="candidate-id">' + esc(c.candidate_id) + '</span><span>' + status + win + '</span></div>' +
      '<div class="rationale">' + esc(c.rationale) + '</div>' +
      '<div class="meta">exit ' + esc(t.exit_code) + ' · edits ' + esc(item.edit_count) + ' · span ' + esc(item.edit_span_chars) + ' chars</div>' +
      edits + '</article>';
  }

  function renderResult(data) {
    const report = data.report || {};
    const evidence = data.evidence || {};
    const candidates = report.candidates || [];
    const winner = report.winner_id || null;
    summaryEl.className = "";
    summaryEl.innerHTML =
      '<div><strong>' + (winner ? 'Repair accepted' : 'No repair accepted') + '</strong></div>' +
      '<div class="meta">run ' + esc(data.run_id) + ' · ' + esc(data.generated_at_utc) + '</div>' +
      '<p>' + esc(data.evidence_rule) + '</p>' +
      '<p class="meta">Winner policy: ' + esc(evidence.winner_policy) + '</p>';

    metricsEl.style.display = "grid";
    metricsEl.innerHTML =
      metric("Winner", winner || "none") +
      metric("Passed", String(evidence.pass_count) + "/" + String(evidence.candidate_count)) +
      metric("Runtime", String(data.elapsed_ms) + " ms") +
      metric("Backend", report.sandbox || "unknown") +
      metric("Model", data.live_model || "unknown") +
      metric("Baseline", report.baseline && report.baseline.passed ? "PASS" : "FAIL") +
      metric("Cache", data.cached ? "HIT" : "MISS") +
      metric("Release", "v" + String(data.release || "unknown"));

    candidatesEl.className = "candidate-grid";
    candidatesEl.innerHTML = candidates.length
      ? candidates.map(function(x) { return renderCandidate(x, winner); }).join("")
      : '<div class="empty">Planner returned no candidates.</div>';

    rawEl.textContent = JSON.stringify(data, null, 2);
  }

  runButton.addEventListener("click", async function() {
    runButton.disabled = true;
    stateEl.textContent = "Calling Nemotron and testing candidate repairs...";
    try {
      const response = await fetch("/api/demo", { method: "POST" });
      const data = await response.json();
      renderResult(data);
      stateEl.textContent = response.ok ? "Live evidence complete." : "Run completed without a winner.";
    } catch (err) {
      stateEl.textContent = "Request failed.";
      rawEl.textContent = String(err);
    } finally {
      runButton.disabled = false;
    }
  });
</script>
</body>
</html>
"""

_INDEX = (
    _INDEX_TEMPLATE
    .replace("__VERSION__", html.escape(__version__))
    .replace("__SOURCE__", html.escape((_FIXTURE / "calc.py").read_text(encoding="utf-8")))
    .replace("__REPO__", html.escape(_PUBLIC_REPO))
)


@app.get("/")
def index():
    return _INDEX, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.get("/healthz")
def healthz():
    return jsonify(
        status="ok",
        version=__version__,
        model=_MODEL,
        fixture="examples/buggy_calc",
        public_repo=_PUBLIC_REPO,
        accepts_user_code=False,
    )


@app.post("/api/demo")
def demo():
    global _cached_at, _cached_payload

    now = time.monotonic()
    if _cached_payload is not None and now - _cached_at < _CACHE_TTL_SECONDS:
        return jsonify(
            {
                **_cached_payload,
                "cached": True,
                "cache_age_seconds": round(now - _cached_at, 2),
            }
        )

    if not os.getenv("NEBIUS_API_KEY"):
        return jsonify(error="demo server is not configured for Token Factory inference"), 503

    if not _LOCK.acquire(blocking=False):
        return jsonify(error="a repair experiment is already running"), 429

    started = time.perf_counter()
    try:
        report = run_repair(
            repo=_FIXTURE,
            issue=_ISSUE,
            test_command=_TEST_COMMAND,
            planner=NemotronPlanner(),
            sandbox=LocalSandbox(timeout_seconds=30, deny_network=True),
            candidate_count=3,
        )
        report_dict = report.to_dict()
        candidates = report_dict.get("candidates", [])
        pass_count = sum(1 for candidate in candidates if candidate.get("passed"))
        payload = {
            "run_id": uuid.uuid4().hex[:12],
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "release": __version__,
            "live_model": _MODEL,
            "fixture": "examples/buggy_calc",
            "public_repo": _PUBLIC_REPO,
            "report": report_dict,
            "evidence": {
                "candidate_count": len(candidates),
                "pass_count": pass_count,
                "winner_policy": "fewest edits, then smallest replaced source span, then candidate_id",
                "baseline_expected_to_fail": True,
            },
            "evidence_rule": "winner_id is present only when the unchanged test command passes",
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "cached": False,
        }
        _cached_payload = payload
        _cached_at = time.monotonic()
        return jsonify(payload), 200 if report.winner_id else 422
    except Exception as exc:
        app.logger.exception("live demo failed")
        return jsonify(error=type(exc).__name__), 500
    finally:
        _LOCK.release()


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
