#!/usr/bin/env python3
"""Regenerate the cross-model comparison dashboards: baseline generation
quality (structural + LLM-judge metrics), modifiability score, and pattern
fidelity, for each dataset that has per-model results.

- dashboard/compare.html           <- dataset/student_projects (19 projects)
- dashboard/compare_microservice.html <- dataset/MicroserviceDataset (20 projects)

Self-contained like generate.py: data is embedded inline, diagrams referenced
by relative path back into the repo. Modifiability/pattern-fidelity coverage
on MicroserviceDataset varies per model depending on whether that pipeline
stage has been run for it yet (e.g. DeepSeek already has modifiability
reports there from an earlier session; a fresh model won't until its own
modifiability batch is run) — build_modifiability/build_pattern_fidelity
already report partial (done < total) or all-zero coverage correctly either
way, and the template renders both as "no data" rather than crashing.

Usage: python dashboard/compare.py
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent

NUMERIC_BASELINE_FIELDS = [
    "node_f1", "edge_f1", "ged", "boundary_accuracy",
    "completeness", "accuracy", "rationality", "readability",
]


def list_projects(dataset_dir_rel: str) -> list[str]:
    d = REPO / dataset_dir_rel
    if not d.exists():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir() and not p.name.startswith("."))


def load_baseline_rows(csv_rel: str, projects: list[str]) -> dict[str, dict]:
    """Row per project, keyed by name. headless_report.csv accumulates rows
    from many unrelated runs across datasets (append-mode) — the last row
    for a given project name is its most current data, and iterating in
    file order naturally gives last-occurrence-wins when building a dict.
    Only rows whose project is in `projects` are kept.
    """
    path = REPO / csv_rel
    if not path.exists():
        return {}
    by_name: dict[str, dict] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("project") in projects:
                by_name[row["project"]] = row
    return by_name


def mean_and_count(values: list) -> tuple[float | None, int]:
    nums = []
    for v in values:
        if v in (None, ""):
            continue
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            continue
    if not nums:
        return None, 0
    return sum(nums) / len(nums), len(nums)


def build_baseline(csv_rel: str, projects: list[str]) -> dict:
    rows = load_baseline_rows(csv_rel, projects)
    # "evaluated" is the status run_headless.py --eval-only writes back after
    # scoring an already-generated project — it only ever touches rows that
    # were already a successful generation, so it counts as generated too.
    success = sum(1 for r in rows.values() if r.get("status") in ("success", "skipped", "evaluated"))
    metrics = {}
    for field in NUMERIC_BASELINE_FIELDS:
        mean, n = mean_and_count([r.get(field) for r in rows.values()])
        metrics[field] = {"mean": mean, "n": n}
    return {
        "total": len(projects),
        "generated": success,
        "metrics": metrics,
    }


def build_modifiability(mod_dir_rel: str, projects: list[str]) -> dict:
    mod_dir = REPO / mod_dir_rel
    scores, normalized = [], []
    done = 0
    for name in projects:
        report_path = mod_dir / name / "modifiability" / "report.json"
        if not report_path.exists():
            continue
        try:
            r = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        scenarios = r.get("scenarios", [])
        # A report.json can exist but be entirely invalid — e.g. every
        # scenario errored out (a connection drop mid-run) while the batch
        # runner still wrote a "complete" report with modifiability_score=0.
        # That 0 is not a real result and must not be averaged in as if the
        # project were genuinely cheap to modify. Treat it as not-yet-done.
        if scenarios and all(s.get("error") for s in scenarios):
            continue
        done += 1
        if r.get("modifiability_score") is not None:
            scores.append(r["modifiability_score"])
        if r.get("normalized_modifiability_score") is not None:
            normalized.append(r["normalized_modifiability_score"])
    score_mean, score_n = mean_and_count(scores)
    norm_mean, norm_n = mean_and_count(normalized)
    return {
        "total": len(projects),
        "done": done,
        "score": {"mean": score_mean, "n": score_n},
        "normalized": {"mean": norm_mean, "n": norm_n},
    }


def build_pattern_fidelity(output_dir_rel: str, projects: list[str]) -> dict:
    """Average, across every project, the pattern_judge.py per-project
    score (itself the average of every KB-matched pattern's 1-5 application
    score in that project's architecture.json). Keeps the full per-project /
    per-pattern breakdown too, so the dashboard can drill down into it."""
    output_dir = REPO / output_dir_rel
    project_scores = []
    n_patterns_total = 0
    projects_out = {}
    for name in projects:
        path = output_dir / name / "pattern_scores.json"
        if not path.exists():
            continue
        try:
            r = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        projects_out[name] = r
        if r.get("project_score") is not None:
            project_scores.append(r["project_score"])
            n_patterns_total += r.get("n_patterns", 0)
    mean, n = mean_and_count(project_scores)
    return {
        "mean": mean, "n": n, "total": len(projects),
        "n_patterns_total": n_patterns_total, "projects": projects_out,
    }


def build_dataset(projects: list[str], models_config: list[tuple[str, str, str, str]], dataset_label: str) -> dict:
    models = []
    for key, label, baseline_csv, mod_dir in models_config:
        models.append({
            "key": key,
            "label": label,
            "baseline": build_baseline(baseline_csv, projects),
            "modifiability": build_modifiability(mod_dir, projects),
            "pattern_fidelity": build_pattern_fidelity(mod_dir, projects),
        })
    return {
        "dataset_total": len(projects),
        "dataset_label": dataset_label,
        "models": models,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }


def write_compare_page(out_name: str, data: dict) -> None:
    template = (DASHBOARD_DIR / "compare_template.html").read_text(encoding="utf-8")
    out = template.replace("/*__DATA__*/", json.dumps(data, indent=None, ensure_ascii=False))
    (DASHBOARD_DIR / out_name).write_text(out, encoding="utf-8")
    print(f"wrote {DASHBOARD_DIR / out_name}")


# (key, label, baseline_csv relative to REPO, modifiability_dir relative to REPO)
STUDENT_PROJECTS_MODELS = [
    ("deepseek", "DeepSeek-Flash", "results/reports/student_projects_report.csv", "results/student_projects"),
    ("kimi", "Kimi K2.7-Code", "results/reports/kimi_student_projects_report.csv", "results/student_projects_kimi_full"),
    ("gemma", "Gemma-4-26B-A4B", "results/reports/gemma4_26b_a4b_student_projects_report.csv", "results/gemma4_26b_a4b/student_projects"),
    ("qwen", "Qwen3.8-27B", "results/reports/qwen38_27b_student_projects_report.csv", "results/qwen38_27b/student_projects"),
]

# Pattern-KB matching hasn't been run against MicroserviceDataset for any
# model (pattern_fidelity comes back n=0 here); modifiability coverage
# varies per model — see the module docstring.
MICROSERVICE_DATASET_MODELS = [
    ("deepseek", "DeepSeek-Flash", "results/reports/microservice_dataset_report.csv", "results/microservice_dataset"),
    ("kimi", "Kimi K2.7-Code", "results/reports/microservice_dataset_kimi_report.csv", "results/microservice_dataset_kimi"),
    ("gemma", "Gemma-4-26B-A4B", "results/reports/microservice_dataset_gemma_report.csv", "results/microservice_dataset_gemma"),
    ("qwen", "Qwen3.8-27B", "results/reports/qwen38_27b_microservice_dataset_report.csv", "results/qwen38_27b/microservice_dataset"),
]


def main():
    student_projects = list_projects("dataset/student_projects")
    write_compare_page(
        "compare.html",
        build_dataset(student_projects, STUDENT_PROJECTS_MODELS, "dataset/student_projects"),
    )

    microservice_projects = list_projects("dataset/MicroserviceDataset")
    write_compare_page(
        "compare_microservice.html",
        build_dataset(microservice_projects, MICROSERVICE_DATASET_MODELS, "dataset/MicroserviceDataset"),
    )


if __name__ == "__main__":
    main()
