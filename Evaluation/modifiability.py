"""
modifiability.py — orchestrates the modifiability-analysis pipeline for one
project: generate future scenarios, modify the architecture for each,
measure graph edit distance against the baseline diagram, and aggregate into
a weighted Modifiability Score (lower is better).
"""
from __future__ import annotations

import json
from pathlib import Path

from Evaluation.modifiability_graph import build_graph, compute_ged
from Evaluation.modifiability_scenarios import (
    generate_scenarios,
    modify_architecture,
    render_scenario_diagram,
)
from Evaluation.uml_parser import UMLParser


def _load_original(run_dir: str, project_name: str) -> tuple[dict, dict]:
    """Read architecture.json + parse component_diagram.puml for
    project_name. Raises FileNotFoundError (with a clear message) if either
    is missing.
    """
    project_dir = Path(run_dir) / project_name
    arch_path = project_dir / "architecture.json"
    puml_path = project_dir / "component_diagram.puml"
    if not arch_path.exists() or not puml_path.exists():
        raise FileNotFoundError(
            f"Missing {arch_path} or {puml_path} — run the diagram pipeline "
            f"for '{project_name}' before running modifiability analysis."
        )
    architecture = json.loads(arch_path.read_text(encoding="utf-8"))
    parsed_original = UMLParser().parse(puml_path.read_text(encoding="utf-8"))
    return architecture, parsed_original


def _score_one_scenario(scenario: dict, architecture: dict, g_original, timeout: float) -> dict:
    """Run the edit -> render -> parse -> GED steps for one scenario. Never
    raises — records an "error" key in the returned dict on any failure
    instead, so one bad scenario doesn't abort the whole batch.
    """
    try:
        modified_arch = modify_architecture(architecture, scenario["description"])
        rendered = render_scenario_diagram(modified_arch)
        parsed_modified = UMLParser().parse(rendered)
        g_modified = build_graph(parsed_modified)

        if g_modified.number_of_nodes() == 0 and g_original.number_of_nodes() > 0:
            raise ValueError("Rendered diagram for this scenario has no parseable components")

        ged = compute_ged(g_original, g_modified, timeout=timeout)
        weighted_ged = scenario["weight"] * ged if ged is not None else None
    except Exception as e:
        print(f"[modifiability] scenario failed: {scenario.get('description', '')[:60]!r} — {e}")
        return {**scenario, "error": str(e), "ged": None, "exact": False, "weighted_ged": None}

    if ged is None:
        print(f"[modifiability] GED inconclusive (timeout) for: {scenario.get('description', '')[:60]!r}")
        return {**scenario, "ged": None, "exact": False, "weighted_ged": None}

    return {**scenario, "ged": ged, "exact": True, "weighted_ged": weighted_ged}


def run(
    project_name: str,
    n_scenarios: int = 5,
    timeout: float = 10.0,
    run_dir: str = "run",
    dataset_dir: str = "dataset/student_projects",
) -> dict:
    architecture, parsed_original = _load_original(run_dir, project_name)
    g_original = build_graph(parsed_original)

    input_path = Path(dataset_dir) / project_name / "input.txt"
    input_text = input_path.read_text(encoding="utf-8")

    scenarios = generate_scenarios(input_text, n=n_scenarios)

    scored = [_score_one_scenario(s, architecture, g_original, timeout) for s in scenarios]

    modifiability_score = sum(
        s["weighted_ged"] for s in scored if s.get("weighted_ged") is not None
    )
    by_magnitude: dict = {}
    for s in scored:
        if s.get("weighted_ged") is None:
            continue
        magnitude = s.get("magnitude", "unknown")
        by_magnitude[magnitude] = by_magnitude.get(magnitude, 0.0) + s["weighted_ged"]

    report = {
        "project": project_name,
        "n_scenarios": n_scenarios,
        "scenarios": scored,
        "modifiability_score": round(modifiability_score, 2),
        "by_magnitude": {k: round(v, 2) for k, v in by_magnitude.items()},
    }

    report_dir = Path(run_dir) / project_name / "modifiability"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run modifiability analysis for a project.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--n-scenarios", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    result = run(args.project, n_scenarios=args.n_scenarios, timeout=args.timeout)
    print(f"Modifiability Score for {args.project}: {result['modifiability_score']}")
