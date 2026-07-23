"""
modifiability.py — orchestrates the modifiability-analysis pipeline for one
project: generate future scenarios, modify the architecture for each,
measure graph edit distance against the baseline diagram, and aggregate into
a weighted Modifiability Score (lower is better).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Callable

from Evaluation.modifiability_graph import build_graph, compute_ged
from Evaluation.modifiability_scenarios import (
    generate_scenarios,
    modify_architecture,
    render_scenario_diagram,
)
from Evaluation.uml_parser import UMLParser


def _load_original(run_dir: str, project_name: str) -> tuple[dict, dict, str]:
    """Read architecture.json + parse component_diagram.puml for
    project_name. Raises FileNotFoundError (with a clear message) if either
    is missing. Returns (architecture, parsed_original, original_puml_text)
    — the raw text is kept so per-scenario rendering can adapt it directly
    (see render_scenario_diagram's original_diagram parameter) rather than
    regenerating a diagram from scratch.
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
    original_puml_text = puml_path.read_text(encoding="utf-8")
    parsed_original = UMLParser().parse(original_puml_text)
    return architecture, parsed_original, original_puml_text


def _load_or_generate_scenarios(
    report_dir: Path,
    input_text: str,
    n_scenarios: int,
    regenerate_scenarios: bool,
    cost_tracker: list[float] | None = None,
) -> list[dict]:
    """Once a project's scenarios are generated, they're saved to
    scenarios.json and kept fixed across future runs — re-scoring (e.g.
    after tweaking timeout, or after the architecture changed) compares
    against the SAME scenarios by default, so results stay comparable run to
    run. Pass regenerate_scenarios=True to explicitly roll a fresh set.
    """
    scenarios_path = report_dir / "scenarios.json"
    if scenarios_path.exists() and not regenerate_scenarios:
        print(f"[modifiability] reusing saved scenarios from {scenarios_path}")
        return json.loads(scenarios_path.read_text(encoding="utf-8"))

    scenarios = generate_scenarios(input_text, n=n_scenarios, cost_tracker=cost_tracker)
    scenarios_path.write_text(json.dumps(scenarios, indent=2, ensure_ascii=False), encoding="utf-8")
    return scenarios


def _build_updated_spec(original_input_text: str, new_user_story: str) -> str:
    """Append one new user story to the end of the existing spec's numbered
    list, continuing the numbering. This is the "new specs" artifact saved
    per scenario — the exact input that drove the modified architecture,
    alongside the resulting architecture.json/component_diagram.puml.
    """
    existing_numbers = [
        int(m.group(1)) for m in re.finditer(r"(?m)^\s*(\d+)\.\s", original_input_text)
    ]
    next_number = max(existing_numbers, default=0) + 1
    return original_input_text.rstrip("\n") + f"\n{next_number}. {new_user_story}\n"


def _score_one_scenario(
    scenario: dict,
    architecture: dict,
    g_original,
    timeout: float,
    original_puml_text: str,
    input_text: str,
    scenario_dir: Path | None = None,
    cost_tracker: list[float] | None = None,
) -> dict:
    """Run the edit -> render -> parse -> GED steps for one scenario. Never
    raises — records an "error" key in the returned dict on any failure
    instead, so one bad scenario doesn't abort the whole batch.

    original_puml_text: the project's existing rendered diagram, passed to
        render_scenario_diagram so the new version adapts it in place
        (same aliases/grouping for anything unchanged) rather than
        regenerating a diagram from scratch for every scenario.
    input_text: the project's existing spec (system description + user
        stories). Used to save a full "updated spec" artifact — the original
        stories plus this scenario's new one — alongside the modified
        architecture/diagram, so the exact input that drove each variation
        is on disk, not just the isolated scenario description.
    scenario_dir: if given, the intermediate modified architecture.json and
        rendered component_diagram.puml are written there as soon as each is
        produced — so a partial artifact (e.g. the edit succeeded but the
        render failed) is still saved for inspection, not just the final
        aggregated report.
    cost_tracker: if given, forwarded to each LLM call so their USD costs
        accumulate into it (see Evaluation.modifiability_scenarios._complete).
    """
    try:
        if scenario_dir is not None:
            scenario_dir.mkdir(parents=True, exist_ok=True)
            (scenario_dir / "input.txt").write_text(
                _build_updated_spec(input_text, scenario["description"]), encoding="utf-8"
            )

        modified_arch = modify_architecture(
            architecture, scenario["description"], cost_tracker=cost_tracker
        )
        if scenario_dir is not None:
            (scenario_dir / "architecture.json").write_text(
                json.dumps(modified_arch, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        rendered = render_scenario_diagram(
            modified_arch, original_diagram=original_puml_text, cost_tracker=cost_tracker
        )
        if scenario_dir is not None:
            (scenario_dir / "component_diagram.puml").write_text(rendered, encoding="utf-8")

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
    on_progress: Callable[[int, int, dict], None] | None = None,
    regenerate_scenarios: bool = False,
) -> dict:
    """
    on_progress: optional callback invoked as on_progress(completed, total,
        result) immediately after each scenario is scored, so a caller (e.g.
        a Streamlit UI) can report incremental progress instead of waiting
        silently for the whole batch.
    regenerate_scenarios: once scenarios are generated for a project, they're
        saved to {run_dir}/{project_name}/modifiability/scenarios.json and
        reused on every subsequent call by default (kept fixed so results are
        comparable across re-scoring runs). Set True to roll a fresh set.
    """
    start_time = time.time()
    cost_tracker: list[float] = []

    architecture, parsed_original, original_puml_text = _load_original(run_dir, project_name)
    g_original = build_graph(parsed_original)

    input_path = Path(dataset_dir) / project_name / "input.txt"
    input_text = input_path.read_text(encoding="utf-8")

    report_dir = Path(run_dir) / project_name / "modifiability"
    report_dir.mkdir(parents=True, exist_ok=True)

    scenarios = _load_or_generate_scenarios(
        report_dir, input_text, n_scenarios, regenerate_scenarios, cost_tracker=cost_tracker
    )

    total = len(scenarios)
    scored = []
    for i, s in enumerate(scenarios, start=1):
        scenario_dir = report_dir / f"scenario_{i:02d}"
        result = _score_one_scenario(
            s, architecture, g_original, timeout, original_puml_text, input_text,
            scenario_dir=scenario_dir, cost_tracker=cost_tracker,
        )
        result["artifacts_dir"] = str(scenario_dir)
        scored.append(result)
        if on_progress is not None:
            on_progress(i, total, result)

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
        "n_scenarios": total,
        "scenarios": scored,
        "modifiability_score": round(modifiability_score, 2),
        "by_magnitude": {k: round(v, 2) for k, v in by_magnitude.items()},
        "original_node_count": g_original.number_of_nodes(),
        "original_edge_count": g_original.number_of_edges(),
        "execution_time_seconds": round(time.time() - start_time, 2),
        "total_cost_usd": round(sum(cost_tracker), 4),
    }

    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"[modifiability] {project_name}: Time: {report['execution_time_seconds']:.2f}s "
        f"| Cost: ${report['total_cost_usd']:.4f}"
    )

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run modifiability analysis for a project.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--n-scenarios", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--regenerate-scenarios", action="store_true",
        help="Roll a fresh scenario set instead of reusing any saved scenarios.json",
    )
    args = parser.parse_args()

    result = run(
        args.project, n_scenarios=args.n_scenarios, timeout=args.timeout,
        regenerate_scenarios=args.regenerate_scenarios,
    )
    print(f"Modifiability Score for {args.project}: {result['modifiability_score']}")
