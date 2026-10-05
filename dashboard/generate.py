#!/usr/bin/env python3
"""Regenerate dashboard/index.html from the live run-progress state under
dashboard/run_progress/ (local runs) and dashboard/run_progress/remote/
(synced in from the remote runner — see sync_remote.sh).
Self-contained: all data is embedded inline in the HTML (no fetch, no server
needed) and diagrams are referenced by relative path back into the repo, so
`open dashboard/index.html` works straight from a checkout.

Usage: python dashboard/generate.py
"""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent


def rel(path: Path) -> str:
    """Path relative to dashboard/, for use as an <img src> / href (dashboard/
    and results/ are siblings under REPO, so this needs a "../" walk-up)."""
    return os.path.relpath(path.resolve(), DASHBOARD_DIR.resolve())


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def vllm_stats(model: str) -> dict:
    """Read lightweight throughput counters from the known local vLLM hosts."""
    endpoint = "192.168.0.182:8000" if "gemma" in (model or "").lower() else "192.168.0.155:8000" if "qwen" in (model or "").lower() else None
    if not endpoint:
        return {}
    try:
        text = urllib.request.urlopen(f"http://{endpoint}/metrics", timeout=2).read().decode()
        def value(name):
            m = re.search(rf"^vllm:{name}(?:\{{[^}}]*\}})?\s+([0-9.eE+-]+)$", text, re.MULTILINE)
            return float(m.group(1)) if m else None
        tok_time = value("request_time_per_output_token_seconds_sum")
        tok_count = value("request_time_per_output_token_seconds_count")
        tok_s = (tok_count / tok_time) if tok_time and tok_count else None
        return {"host": endpoint, "output_tokens_per_second": tok_s,
                "observed_requests": int(tok_count or 0)}
    except Exception:
        return {}


def build_generation_runs() -> list[dict]:
    """Load generic run-state files emitted by run_headless.py — both the
    ones written directly on this machine (dashboard/run_progress/*.json)
    and the ones synced in from the remote runner (dashboard/run_progress/
    remote/*.json, populated by sync_remote.sh). Which directory a
    file came from is the origin signal (is_remote), not its filename.
    """
    progress_dir = DASHBOARD_DIR / "run_progress"
    if not progress_dir.exists():
        return []
    runs = []
    for source_dir, is_remote in ((progress_dir, False), (progress_dir / "remote", True)):
        if not source_dir.exists():
            continue
        for path in source_dir.glob("*.json"):
            state = load_json(path)
            if not isinstance(state, dict) or not isinstance(state.get("projects"), list):
                continue
            state["is_remote"] = is_remote
            state["progress_file"] = rel(path)
            output_value = state.get("output")
            if output_value:
                output_dir = Path(output_value)
                if not output_dir.is_absolute():
                    output_dir = REPO / output_dir
                for project in state["projects"]:
                    png = output_dir / project.get("name", "") / "component_diagram.png"
                    project["diagram_png"] = (
                        f"{rel(png)}?v={png.stat().st_mtime_ns}" if png.is_file() else None
                    )
            if state.get("backend") == "vllm":
                stats = vllm_stats(state.get("model", ""))
                if stats:
                    state["vllm_stats"] = stats
                    completed = [p for p in state["projects"] if p.get("status") in ("success", "skipped")]
                    pending = [p for p in state["projects"] if p.get("status") in ("pending", "running", "waiting")]
                    times = [float(p["time_seconds"]) for p in completed if p.get("time_seconds") is not None]
                    if times:
                        state["estimated_remaining_seconds"] = sum(times) / len(times) * len(pending)
            runs.append(state)
    return sorted(runs, key=lambda r: r.get("started_at", ""), reverse=True)


def main():
    generation_runs = build_generation_runs()
    live = any(r.get("status") in ("running", "waiting") for r in generation_runs)

    data = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generation_runs": generation_runs,
        "live": live,
    }

    template = (DASHBOARD_DIR / "template.html").read_text(encoding="utf-8")
    out = template.replace(
        "/*__DATA__*/",
        json.dumps(data, indent=None, ensure_ascii=False),
    )
    (DASHBOARD_DIR / "index.html").write_text(out, encoding="utf-8")
    print(f"wrote {DASHBOARD_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
