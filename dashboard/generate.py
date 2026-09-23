#!/usr/bin/env python3
"""Regenerate dashboard/index.html from the current results/ + Evaluation/outputs/
state. Self-contained: all data is embedded inline in the HTML (no fetch, no
server needed) and diagrams are referenced by relative path back into the
repo, so `open dashboard/index.html` works straight from a checkout.

Usage: python dashboard/generate.py
"""
import csv
import json
import os
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent

DATASETS = [
    ("student_projects", "dataset/student_projects", "results/student_projects"),
    ("open_source_projects", "dataset/open_source_projects", "results/open_source_projects"),
    # Was "MicroserviceDataset" (no "dataset/" prefix) — that path doesn't
    # exist on disk, so this panel silently showed 0/0 projects. The real
    # dataset lives at dataset/MicroserviceDataset, same as the other two.
    ("microservice_dataset", "dataset/MicroserviceDataset", "results/microservice_dataset"),
]


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
def project_names(rel_dir: str) -> list[str]:
    p = REPO / rel_dir
    if not p.exists():
        return []
    return sorted(d.name for d in p.iterdir() if d.is_dir() and not d.name.startswith("."))


def build_generation_runs() -> list[dict]:
    """Load generic run-state files emitted by run_headless.py."""
    progress_dir = DASHBOARD_DIR / "run_progress"
    if not progress_dir.exists():
        return []
    runs = []
    for path in progress_dir.glob("*.json"):
        state = load_json(path)
        if not isinstance(state, dict) or not isinstance(state.get("projects"), list):
            continue
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


def build_dataset(key: str, dataset_rel: str, output_rel: str) -> dict:
    total_names = project_names(dataset_rel)
    report_path = REPO / "results" / "reports" / f"{key}_report.csv"
    rows_by_name = {}
    if report_path.exists():
        with open(report_path, newline="") as f:
            rows_by_name = {r["project"]: r for r in csv.DictReader(f)}

    projects = []
    for name in total_names:
        row = rows_by_name.get(name)
        out_dir = REPO / output_rel / name
        entry = {
            "name": name,
            "status": "pending",
            "time_seconds": None, "cost": None,
            "node_f1": None, "edge_f1": None, "ged": None, "boundary_accuracy": None,
            "completeness": None, "accuracy": None, "rationality": None, "readability": None,
            "error": None,
            "diagram_png": None, "summary_md": None,
            "judge_alignment": None, "arch_score": None,
        }
        if row:
            entry["status"] = "success" if row["status"] in ("success", "skipped") else "failed"
            entry["time_seconds"] = float(row["time_seconds"]) if row.get("time_seconds") else None
            entry["cost"] = float(row["cost"]) if row.get("cost") else None
            for f in ("node_f1", "edge_f1", "ged", "boundary_accuracy"):
                entry[f] = float(row[f]) if row.get(f) else None
            for f in ("completeness", "accuracy", "rationality", "readability"):
                entry[f] = int(row[f]) if row.get(f) else None
            entry["error"] = row.get("error") or None

        png = out_dir / "component_diagram.png"
        if png.exists():
            entry["diagram_png"] = rel(png)
        md = out_dir / "architecture_summary.md"
        if md.exists():
            entry["summary_md"] = md.read_text(encoding="utf-8", errors="replace")

        eval_out = REPO / "Evaluation" / "outputs" / name
        entry["judge_alignment"] = load_json(eval_out / "judge_alignment.json")
        entry["arch_score"] = load_json(eval_out / "arch_score.json")

        projects.append(entry)

    return {"key": key, "label": dataset_rel, "total": len(total_names), "projects": projects}


def find_active_baseline_project() -> str | None:
    """Best-effort: the project name currently being generated via
    `run_headless.py --project <name>`, read from live process state.

    run_headless.py's baseline-generation phase works in a temp workspace
    and only copies anything into run_kimi_baseline/<project>/ once it's
    essentially done — often several minutes in — so filesystem state alone
    can't distinguish "actively generating this project" from "hasn't
    started" during that whole window (see build_kimi_baseline). The
    subprocess's own command line has the answer directly, no polling of
    internal state needed. Returns None if no such process is running right
    now (nothing to show, or the batch is between phases / in the
    modifiability step, which runs in-process rather than as a subprocess).
    """
    try:
        out = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return None
    m = re.search(r"run_headless\.py.*?--project\s+(\S+)", out)
    return m.group(1) if m else None


def build_kimi_baseline(
    output_dir_rel: str, report_csv_rel: str = "headless_report.csv",
    active_project: str | None = None,
) -> dict:
    """Status of the Kimi from-scratch baseline-architecture generation phase
    (run via run_headless.py --output <output_dir_rel>, same pipeline/CSV
    report format as the main DeepSeek datasets, just a different actor
    model and a project-name-keyed lookup since student_projects names don't
    collide with the other datasets sharing headless_report.csv).

    A project is "success" once its component_diagram.puml exists (the
    pipeline's own completion signal); "running" if its output folder exists
    but that file doesn't yet (mid-generation, or interrupted); "pending" if
    nothing has been written for it at all. Cost/time come from the LAST
    matching row in the CSV for that project name (later rows win, in case a
    project was retried), when a row exists.
    """
    names = project_names("dataset/student_projects")
    out_dir = REPO / output_dir_rel

    rows_by_name: dict = {}
    report_path = REPO / report_csv_rel
    if report_path.exists():
        with open(report_path, newline="") as f:
            for row in csv.DictReader(f):
                rows_by_name[row["project"]] = row  # last one wins

    projects = []
    for name in names:
        project_dir = out_dir / name
        puml = project_dir / "component_diagram.puml"
        row = rows_by_name.get(name)
        entry = {
            "name": name, "status": "pending",
            "time_seconds": None, "cost": None,
            "diagram_png": None,
        }
        if puml.exists():
            entry["status"] = "success"
            png = project_dir / "component_diagram.png"
            if png.exists():
                entry["diagram_png"] = rel(png)
        elif project_dir.exists():
            entry["status"] = "running"
        elif name == active_project:
            # Confirmed via the live subprocess command line (see
            # find_active_baseline_project) — the agent is working on this
            # project right now even though its output folder doesn't
            # exist on disk yet.
            entry["status"] = "running"
        if row:
            entry["time_seconds"] = float(row["time_seconds"]) if row.get("time_seconds") else None
            entry["cost"] = float(row["cost"]) if row.get("cost") else None
            if entry["status"] == "pending" and row.get("status") == "error":
                entry["status"] = "failed"
        projects.append(entry)

    return {"projects": projects, "total": len(names)}


def build_modifiability(
    run_dir_rel: str = "results/student_projects",
    dataset_dir_rel: str = "dataset/student_projects",
) -> dict:
    """run_dir_rel: mirrors Evaluation.modifiability.run()'s run_dir — pass
    e.g. "results/student_projects_kimi" to build the same shape for a
    different actor model's run, kept in its own folder alongside the
    default (DeepSeek) one so neither overwrites the other.

    dataset_dir_rel: mirrors Evaluation.modifiability.run()'s dataset_dir —
    which dataset's project list to enumerate (student_projects,
    open_source_projects, or MicroserviceDataset all have the same
    {project}/input.txt shape modifiability needs).

    A project with no report.json yet is "pending" if nothing has been
    written for it at all, or "running" if some of its scenario_NN/
    component_diagram.puml files already exist — i.e. a batch job is
    partway through it right now. n_scenarios_expected comes from
    scenarios.json (written before any scenario is scored) so the live
    progress bar has a real denominator even before report.json exists.
    """
    names = project_names(dataset_dir_rel)
    mod_run_dir = REPO / run_dir_rel
    projects = []
    for name in names:
        report_path = mod_run_dir / name / "modifiability" / "report.json"
        if not report_path.exists():
            scenarios_path = mod_run_dir / name / "modifiability" / "scenarios.json"
            expected = load_json(scenarios_path)
            n_expected = len(expected) if isinstance(expected, list) else None
            rendered = sorted((mod_run_dir / name / "modifiability").glob("scenario_*/component_diagram.puml")) \
                if (mod_run_dir / name / "modifiability").exists() else []
            if rendered:
                projects.append({
                    "name": name, "status": "running",
                    "n_scenarios_done": len(rendered), "n_scenarios_expected": n_expected,
                })
            else:
                projects.append({
                    "name": name, "status": "pending",
                    "n_scenarios_done": 0, "n_scenarios_expected": n_expected,
                })
            continue
        r = load_json(report_path)
        if r is None:
            projects.append({"name": name, "status": "pending", "n_scenarios_done": 0, "n_scenarios_expected": None})
            continue

        scenarios = []
        for i, s in enumerate(r.get("scenarios", []), start=1):
            scenario_dir = mod_run_dir / name / "modifiability" / f"scenario_{i:02d}"
            png = scenario_dir / "component_diagram.png"
            scenarios.append({
                "index": i,
                "description": s.get("description"),
                "weight": s.get("weight"),
                "magnitude": s.get("magnitude"),
                "new_user_stories": s.get("new_user_stories"),
                "removed_user_story_numbers": s.get("removed_user_story_numbers"),
                "ged": s.get("ged"),
                "weighted_ged": s.get("weighted_ged"),
                "error": s.get("error"),
                "diagram_png": rel(png) if png.exists() else None,
            })

        own_weighted = [s["weighted_ged"] for s in scenarios if s.get("weighted_ged") is not None]
        own_max = max(own_weighted) if own_weighted else None
        score = r.get("modifiability_score")

        # The project's own baseline diagram within *this* run's directory —
        # was hardcoded to results/student_projects/<name>, which pointed at
        # the wrong (or a nonexistent) image for any other run_dir_rel.
        original_png = REPO / run_dir_rel / name / "component_diagram.png"

        projects.append({
            "name": name, "status": "success",
            "modifiability_score": score,
            "normalized_modifiability_score": r.get("normalized_modifiability_score"),
            "n_scenarios": r.get("n_scenarios"),
            "by_magnitude": r.get("by_magnitude"),
            "cost": r.get("total_cost_usd"),
            "time_seconds": r.get("execution_time_seconds"),
            "original_diagram_png": rel(original_png) if original_png.exists() else None,
            "own_max_case_weighted_ged": round(own_max, 2) if own_max else None,
            "pct_of_own_max_case": round(100 * score / own_max, 1) if (own_max and score is not None) else None,
            "scenarios": scenarios,
        })
    return {"projects": projects}


MODIFIABILITY_RUNS = [
    ("deepseek", "DeepSeek-Flash", "results/student_projects", "deepseek/deepseek-flash"),
    # "kimi": points at the full from-scratch run (Kimi-generated baseline
    # architecture + Kimi-edited scenarios), not the abandoned edit-only
    # attempt that used to live at results/student_projects_kimi — that
    # folder's partial output (killed mid-run, no report.json) is left on
    # disk untouched but no longer tracked here, so it can't show as
    # perpetually "running" once nothing is actually processing it.
    ("kimi", "Kimi K2.7-Code", "results/student_projects_kimi_full", "moonshot/kimi-k2.7-code"),
]

# DeepSeek modifiability, per dataset — separate from MODIFIABILITY_RUNS
# (which is specifically the student_projects actor-model comparison).
# open_source_projects and microservice_dataset never had modifiability run
# against them until now; each entry here writes into
# results/<dataset>/<project>/modifiability/, right alongside that
# project's existing baseline architecture/diagram from the main pipeline.
MODIFIABILITY_DATASETS = [
    ("student_projects", "Student projects", "dataset/student_projects", "results/student_projects"),
    ("open_source_projects", "Open-source projects", "dataset/open_source_projects", "results/open_source_projects"),
    ("microservice_dataset", "MicroserviceDataset", "dataset/MicroserviceDataset", "results/microservice_dataset"),
]


def main():
    datasets = [build_dataset(*d) for d in DATASETS]
    generation_runs = build_generation_runs()

    modifiability_runs = {}
    actor_models = {}
    for key, label, run_dir_rel, model_str in MODIFIABILITY_RUNS:
        if not (REPO / run_dir_rel).exists():
            continue
        modifiability_runs[key] = {
            **build_modifiability(run_dir_rel),
            "label": label, "run_dir": run_dir_rel, "model": model_str,
        }
        actor_models[key] = {"label": label, "model": model_str}

    kimi_baseline = None
    if (REPO / "run_kimi_baseline").exists():
        kimi_baseline = build_kimi_baseline("run_kimi_baseline", active_project=find_active_baseline_project())

    modifiability_by_dataset = {}
    for key, label, dataset_dir_rel, run_dir_rel in MODIFIABILITY_DATASETS:
        modifiability_by_dataset[key] = {
            **build_modifiability(run_dir_rel, dataset_dir_rel),
            "label": label, "run_dir": run_dir_rel, "dataset_dir": dataset_dir_rel,
        }

    def _incomplete(projects: list) -> bool:
        return bool(projects) and any(p["status"] != "success" for p in projects)

    # True whenever there's unfinished Kimi work or unfinished DeepSeek
    # modifiability on the newer datasets (not yet every project at 100%) —
    # NOT "is a project visibly mid-step right now". The latter raced
    # against real startup latency: run_headless.py's baseline phase can
    # run 2-3 minutes in a temp workspace before it writes anything under
    # run_kimi_baseline/<project>/ at all, so a snapshot taken in that
    # window sees no "running" project and (wrongly) looks finished.
    # student_projects/deepseek is excluded — it's a completed historical
    # baseline and should never keep the page auto-refreshing on its own.
    live = (
        any(r.get("status") in ("running", "waiting") for r in generation_runs)
        or
        _incomplete((kimi_baseline or {}).get("projects", []))
        or _incomplete(modifiability_runs.get("kimi", {}).get("projects", []))
        or _incomplete(modifiability_by_dataset.get("open_source_projects", {}).get("projects", []))
        or _incomplete(modifiability_by_dataset.get("microservice_dataset", {}).get("projects", []))
    )

    data = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "datasets": datasets,
        "generation_runs": generation_runs,
        # Kept for backward compat with the original single-run rendering —
        # always the DeepSeek run, same shape as before this key existed.
        "modifiability": modifiability_runs.get("deepseek", {"projects": []}),
        "modifiability_runs": modifiability_runs,
        "modifiability_by_dataset": modifiability_by_dataset,
        "kimi_baseline": kimi_baseline,
        "actor_models": actor_models,
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
