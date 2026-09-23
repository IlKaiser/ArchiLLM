#!/usr/bin/env python3
"""Run modifiability analysis for a complete, isolated baseline run.

The batch can wait for a ``run_headless.py`` progress file, which lets the
baseline and modifiability phases appear as one model experiment without
touching any other model's result tree.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import multiprocessing
import os
import queue
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ModifiabilityProgress:
    def __init__(self, path: str, projects: list[str], args):
        self.path = Path(path).resolve()
        self.dashboard_live = args.dashboard_live
        self.state = {
            "schema_version": 1,
            "run_id": self.path.stem,
            "phase": "modifiability",
            "status": "waiting" if args.wait_for_progress else "running",
            "pid": os.getpid(),
            "started_at": _now(),
            "updated_at": _now(),
            "finished_at": None,
            "dataset": args.dataset,
            "output": args.run_dir,
            "backend": "vllm" if args.model.startswith("openai/") else "cloud",
            "model": args.model.removeprefix("openai/"),
            "total": len(projects),
            "projects": [
                {
                    "name": name,
                    "status": "pending",
                    "scenarios_completed": 0,
                    "scenarios_total": args.n_scenarios,
                    "time_seconds": None,
                    "cost": None,
                    "error": None,
                }
                for name in projects
            ],
        }
        self.write()

    def project(self, name: str) -> dict:
        return next(p for p in self.state["projects"] if p["name"] == name)

    def set_run_status(self, status: str) -> None:
        self.state["status"] = status
        self.write()

    def update(self, name: str, **values) -> None:
        self.project(name).update(values)
        self.write()

    def finish(self) -> None:
        self.state["status"] = "failed" if any(
            p["status"] in ("error", "failed") for p in self.state["projects"]
        ) else "complete"
        self.state["finished_at"] = _now()
        self.write()

    def write(self) -> None:
        self.state["updated_at"] = _now()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        os.replace(temp, self.path)
        if self.dashboard_live:
            subprocess.run(
                [sys.executable, str(REPO / "dashboard" / "generate.py")],
                cwd=REPO,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


def _run_project(project: str, args, progress_queue) -> dict:
    from Evaluation.modifiability import run

    report_path = Path(args.run_dir) / project / "modifiability" / "report.json"
    if args.skip_existing and report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return {"status": "skipped", "report": report}

    def on_progress(completed: int, total: int, _result: dict) -> None:
        progress_queue.put((project, completed, total))

    try:
        report = run(
            project,
            n_scenarios=args.n_scenarios,
            timeout=args.ged_timeout,
            run_dir=args.run_dir,
            dataset_dir=args.dataset,
            on_progress=on_progress,
        )
        return {"status": "success", "report": report}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _wait_for_baseline(path: Path) -> dict:
    while True:
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(5)
            continue
        if state.get("status") != "running":
            return state
        time.sleep(10)


def _refresh_baseline_diagrams(projects: set[str], run_dir: str) -> None:
    """Re-render diagrams from saved JSON using current deterministic rules.

    This is intentionally done after baseline generation and before
    modifiability so graph comparison and the dashboard use the same current
    pattern-assignment logic, including for projects resumed via
    ``--skip-existing``.
    """
    from run_headless import render_puml_to_png
    from src.diagram_agent import _deterministic_puml_repair, _generate_fallback_puml

    for project in sorted(projects):
        project_dir = Path(run_dir) / project
        architecture = project_dir / "architecture.json"
        diagram = project_dir / "component_diagram.puml"
        if not architecture.exists():
            continue
        _generate_fallback_puml(str(architecture), str(diagram))
        _deterministic_puml_repair(str(diagram))
        render_puml_to_png(diagram)


def parse_args():
    parser = argparse.ArgumentParser(description="Batch modifiability analysis")
    parser.add_argument("--dataset", default="dataset/student_projects")
    parser.add_argument(
        "--project",
        help="Comma-separated project name(s) to process (if omitted, processes all)",
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url")
    parser.add_argument("--api-key", default="local")
    parser.add_argument("--max-output-tokens", type=int, default=8192)
    parser.add_argument("--disable-thinking", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--n-scenarios", type=int, default=5)
    parser.add_argument("--ged-timeout", type=float, default=10.0)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--wait-for-progress")
    parser.add_argument("--progress-file", required=True)
    parser.add_argument("--dashboard-live", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    projects = sorted(p.name for p in Path(args.dataset).iterdir() if p.is_dir())
    if args.project:
        requested = {name.strip() for name in args.project.split(",") if name.strip()}
        unknown = requested - set(projects)
        if unknown:
            raise SystemExit(f"Unknown project name(s): {', '.join(sorted(unknown))}")
        projects = [p for p in projects if p in requested]
    progress = ModifiabilityProgress(args.progress_file, projects, args)

    baseline_state = None
    if args.wait_for_progress:
        print(f"Waiting for baseline run: {args.wait_for_progress}", flush=True)
        baseline_state = _wait_for_baseline(Path(args.wait_for_progress))

    eligible = set(projects)
    if baseline_state:
        eligible = {
            p["name"] for p in baseline_state.get("projects", [])
            if p.get("status") in ("success", "skipped")
        }
        for project in projects:
            if project not in eligible:
                progress.update(project, status="error", error="Baseline generation did not succeed")

    os.environ["LLM_MODEL"] = args.model
    os.environ["LLM_API_KEY"] = args.api_key
    if args.base_url:
        os.environ["LLM_BASE_URL"] = args.base_url.rstrip("/")
    os.environ["LLM_MAX_OUTPUT_TOKENS"] = str(args.max_output_tokens)
    if args.disable_thinking:
        os.environ["LLM_DISABLE_THINKING"] = "1"
    else:
        os.environ.pop("LLM_DISABLE_THINKING", None)
    os.environ["LLM_STREAM_EARLY_STOP"] = "1"
    os.environ.pop("LLM_DETERMINISTIC_RENDER", None)
    progress.set_run_status("running")

    with multiprocessing.Manager() as manager:
        event_queue = manager.Queue()
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            remaining = iter(project for project in projects if project in eligible)

            def submit_next() -> bool:
                try:
                    project = next(remaining)
                except StopIteration:
                    return False
                progress.update(project, status="running", started_at=_now())
                future = pool.submit(_run_project, project, args, event_queue)
                futures[future] = project
                return True

            for _ in range(args.workers):
                if not submit_next():
                    break

            while futures:
                while True:
                    try:
                        project, completed, total = event_queue.get_nowait()
                    except queue.Empty:
                        break
                    progress.update(
                        project,
                        scenarios_completed=completed,
                        scenarios_total=total,
                    )

                done, _ = concurrent.futures.wait(
                    futures, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED
                )
                for future in done:
                    project = futures.pop(future)
                    result = future.result()
                    report = result.get("report", {})
                    progress.update(
                        project,
                        status=result["status"],
                        scenarios_completed=report.get("n_scenarios", 0),
                        time_seconds=report.get("execution_time_seconds"),
                        cost=report.get("total_cost_usd"),
                        error=result.get("error"),
                        finished_at=_now(),
                    )
                    submit_next()

    progress.finish()
    print(f"Modifiability batch {progress.state['status']}", flush=True)


if __name__ == "__main__":
    main()
