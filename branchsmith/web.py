from __future__ import annotations

import os
import shlex
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify

from .engine import run_repair
from .planner import NemotronPlanner
from .sandbox import LocalSandbox

app = Flask(__name__)

_MODEL = "nvidia/nemotron-3-super-120b-a12b"
_FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "buggy_calc"
_LOCK = threading.Lock()
_TEST_COMMAND = f"{shlex.quote(sys.executable)} -m unittest -q"
_CACHE_TTL_SECONDS = 60
_cached_at = 0.0
_cached_payload: dict | None = None

_INDEX = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>BranchSmith Live Demo</title>
  <style>
    body{font-family:system-ui,sans-serif;max-width:900px;margin:48px auto;padding:0 20px;line-height:1.5}
    button{font:inherit;padding:12px 18px;cursor:pointer}
    pre{background:#111;color:#eee;padding:16px;overflow:auto;border-radius:8px;min-height:180px}
    .meta{color:#555}
  </style>
</head>
<body>
  <h1>BranchSmith Live Demo</h1>
  <p>One broken repository. Multiple NVIDIA Nemotron repair hypotheses. Independent test evidence. No passing test, no winner.</p>
  <p class="meta">Hosted demo uses a fixed public fixture and does not execute user-supplied code or commands.</p>
  <button id="run">Run live repair experiment</button>
  <pre id="out">Ready.</pre>
  <script>
    const button=document.getElementById('run');
    const out=document.getElementById('out');
    button.onclick=async()=>{
      button.disabled=true;
      out.textContent='Running Nemotron planner and independent repair tests...';
      try{
        const response=await fetch('/api/demo',{method:'POST'});
        const data=await response.json();
        out.textContent=JSON.stringify(data,null,2);
      }catch(err){
        out.textContent=String(err);
      }finally{
        button.disabled=false;
      }
    };
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    return _INDEX, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.get("/healthz")
def healthz():
    return jsonify(
        status="ok",
        model=_MODEL,
        fixture="examples/buggy_calc",
        accepts_user_code=False,
    )


@app.post("/api/demo")
def demo():
    global _cached_at, _cached_payload

    now = time.monotonic()
    if _cached_payload is not None and now - _cached_at < _CACHE_TTL_SECONDS:
        return jsonify({**_cached_payload, "cached": True})

    if not os.getenv("NEBIUS_API_KEY"):
        return jsonify(error="demo server is not configured for Token Factory inference"), 503

    if not _LOCK.acquire(blocking=False):
        return jsonify(error="a repair experiment is already running"), 429

    try:
        report = run_repair(
            repo=_FIXTURE,
            issue="add() subtracts instead of adding",
            test_command=_TEST_COMMAND,
            planner=NemotronPlanner(),
            sandbox=LocalSandbox(timeout_seconds=30, deny_network=True),
            candidate_count=3,
        )
        payload = {
            "live_model": _MODEL,
            "fixture": "examples/buggy_calc",
            "report": report.to_dict(),
            "evidence_rule": "winner_id is present only when the unchanged test command passes",
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
