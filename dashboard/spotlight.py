#!/usr/bin/env python3
"""Regenerate dashboard/spotlight.html: a deep-dive comparison of one
dataset/student_projects project's modifiability results across all four
actor models (DeepSeek, Kimi, Gemma, Qwen).

The spotlighted project defaults to whichever one has the lowest average
modifiability score across every model that has a complete report.json for
it (i.e. cheapest, most robust to the 5 future-change scenarios) — pass
--project to pick a different one.

Usage: python dashboard/spotlight.py [--project NAME]
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent

# (key, label, output dir relative to REPO, baseline diagram override relative
# to REPO or None to use output_dir/<project>/component_diagram.png)
MODELS = [
    ("deepseek", "DeepSeek-Flash", "results/student_projects", None),
    ("kimi", "Kimi K2.7-Code", "results/student_projects_kimi_full", "run_kimi_baseline"),
    ("gemma", "Gemma-4-26B-A4B", "results/gemma4_26b_a4b/student_projects", None),
    ("qwen", "Qwen3.8-27B", "results/qwen38_27b/student_projects", None),
]


def rel(path: Path) -> str:
    return os.path.relpath(path.resolve(), DASHBOARD_DIR.resolve())


def student_projects() -> list[str]:
    d = REPO / "dataset/student_projects"
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir() and not p.name.startswith("."))


def load_report(output_dir_rel: str, project: str) -> dict | None:
    path = REPO / output_dir_rel / project / "modifiability" / "report.json"
    if not path.exists():
        return None
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    # A report.json can exist but be entirely invalid — e.g. every scenario
    # errored out (a connection drop mid-run) while the batch runner still
    # wrote a "complete" report with modifiability_score=0. Treat that the
    # same as no report at all rather than a fake zero score.
    scenarios = report.get("scenarios", [])
    if scenarios and all(s.get("error") for s in scenarios):
        return None
    return report


def pick_best_project() -> str | None:
    """Lowest average modifiability_score across models that have a
    complete report.json for that project (all 4, so the comparison is
    apples-to-apples)."""
    best_name, best_avg = None, None
    for name in student_projects():
        scores = []
        for key, _, output_dir, _ in MODELS:
            r = load_report(output_dir, name)
            if r and r.get("modifiability_score") is not None:
                scores.append(r["modifiability_score"])
        if len(scores) == len(MODELS):
            avg = sum(scores) / len(scores)
            if best_avg is None or avg < best_avg:
                best_name, best_avg = name, avg
    return best_name


def build_model_data(key: str, label: str, output_dir_rel: str, baseline_override: str | None, project: str) -> dict:
    report = load_report(output_dir_rel, project)
    output_dir = REPO / output_dir_rel / project

    baseline_dir = REPO / baseline_override / project if baseline_override else output_dir
    baseline_png = baseline_dir / "component_diagram.png"

    scenarios = []
    if report:
        for i, s in enumerate(report.get("scenarios", []), start=1):
            scenario_dir = output_dir / "modifiability" / f"scenario_{i:02d}"
            png = scenario_dir / "component_diagram.png"
            scenarios.append({
                "index": i,
                "description": s.get("description"),
                "weight": s.get("weight"),
                "magnitude": s.get("magnitude"),
                "ged": s.get("ged"),
                "weighted_ged": s.get("weighted_ged"),
                "error": s.get("error"),
                "diagram_png": rel(png) if png.is_file() else None,
            })

    return {
        "key": key,
        "label": label,
        "score": report.get("modifiability_score") if report else None,
        "normalized_score": report.get("normalized_modifiability_score") if report else None,
        "baseline_png": rel(baseline_png) if baseline_png.is_file() else None,
        "scenarios": scenarios,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None)
    args = parser.parse_args()

    project = args.project or pick_best_project()
    if not project:
        raise SystemExit("No project has a complete report.json across all 4 models")

    models = [build_model_data(key, label, out_dir, override, project) for key, label, out_dir, override in MODELS]

    data = {
        "project": project,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "models": models,
    }

    template = (DASHBOARD_DIR / "spotlight_template.html").read_text(encoding="utf-8")
    out = template.replace("/*__DATA__*/", json.dumps(data, indent=None, ensure_ascii=False))
    (DASHBOARD_DIR / "spotlight.html").write_text(out, encoding="utf-8")
    print(f"wrote {DASHBOARD_DIR / 'spotlight.html'} (project={project})")


if __name__ == "__main__":
    main()
