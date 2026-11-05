#!/usr/bin/env python3
"""Score ARCHI and the zero-shot plain prompt on dataset/student_projects (or
dataset/MicroserviceDataset with --dataset microservice), for every model, with ONE evaluator (Evaluation/cross_eval.py's judge, cache and
validity rule), so ARCHI and zero-shot numbers are comparable with each other.

Per project and system:
  valid       the diagram exists, parses to >= 1 node and renders on the
              PlantUML server (invalid diagrams are excluded from means).
  rubric      Score_Completeness/Accuracy/Rationality/Readability (1-5),
              judged from the SRS alone, so every project gets them.
              --rubric archi-scope restricts it to what ARCHI draws (services,
              their datastores, inter-service dependencies; prompt_archi_scope.md)
              for every system, and writes scores_archi_scope[_subset].csv.
  structural  Node/Edge F1, GED, boundary accuracy against ref.wsd, only for
              the projects that have a reference diagram.
  patterns    Pattern_Score (mean 1-5) and Pattern_Count, judged from the
              diagram alone (Evaluation/pattern_diagram_judge.py), so systems
              that write no architecture.json are scored on the same evidence.

ARCHI is re-scored here rather than read from results/reports/*.csv, so both
systems are judged by the same model in the same run.

    uv run --with openai --with networkx --with pandas --with python-dotenv \\
        python Evaluation/student_cross_eval.py [--dataset microservice] [--project AD,4-by-4] [--workers 8] \\
        [--rubric archi-scope]
"""
from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pattern_diagram_judge  # noqa: E402
from cross_eval import Evaluator, metrics, parse, write_csv  # noqa: E402

logger = logging.getLogger(__name__)
REPO = Path(__file__).resolve().parent.parent
SYSTEMS = ("archi", "zeroshot")


@dataclass(frozen=True)
class Bench:
    """One dataset: where its projects, reference diagrams, runs and scores live."""
    dataset: Path
    ref_name: str  # reference diagram file inside each project folder
    out: Path
    models: dict[str, tuple[str | None, str | None]]  # model key -> (ARCHI dir, zero-shot dir); None = no run


BENCHES = {
    # Same runs as dashboard/gallery.py.
    "student": Bench(REPO / "dataset" / "student_projects", "ref.wsd", REPO / "results" / "student_cross_eval", {
        "deepseek": ("results/student_projects", "results/deepseek_plain_baseline/student_projects"),
        "kimi": ("run_kimi_baseline", "results/kimi_plain_baseline/student_projects"),
        "gemma": ("results/gemma4_26b_a4b/student_projects", "results/gemma4_26b_a4b_plain_baseline/student_projects"),
        "qwen": ("results/qwen38_27b/student_projects", "results/qwen38_27b_plain_baseline/student_projects"),
        # Zero-shot only, PENTION only (scripts/fable_zeroshot.py).
        "fable": (None, "results/fable_plain_baseline/student_projects"),
        # ArchiLLM (v1, Claude Sonnet 4.5), rendered from its JSON by scripts/archillm_to_puml.py.
        "archillm": ("results/archillm_v1/student_projects", None),
    }),
    # Every project has a reference (diagram.puml); zero-shot exists for DeepSeek only.
    "microservice": Bench(REPO / "dataset" / "MicroserviceDataset", "diagram.puml",
                          REPO / "results" / "microservice_cross_eval", {
        "deepseek": ("results/microservice_dataset", "results/deepseek_plain_baseline/microservice_dataset"),
    }),
}


def list_projects(bench: Bench) -> list[str]:
    return sorted(p.name for p in bench.dataset.iterdir() if p.is_dir() and (p / "input.txt").is_file())


def score_one(ev: Evaluator, bench: Bench, model: str, system: str, project: str, archi_scope: bool = False) -> dict:
    out_dir = bench.models[model][SYSTEMS.index(system)]
    ref_path = bench.dataset / project / bench.ref_name
    base = {"model": model, "system": system, "project": project, "has_ref": ref_path.is_file()}
    pred_path = REPO / out_dir / project / "component_diagram.puml"
    text = pred_path.read_text(errors="ignore") if pred_path.is_file() else ""
    pred = parse(text) if "@startuml" in text else {"nodes": []}
    if not pred.get("nodes") or not ev.renders(text):
        return {**base, "valid": False, "missing": not text}
    prd = (bench.dataset / project / "input.txt").read_text(encoding="utf-8")
    row = {**base, "valid": True, "pred_nodes": len(pred.get("leafnodes") or pred["nodes"]),
           **(ev.rubric_archi_scope(prd, text) if archi_scope else ev.rubric(prd, text)),
           **pattern_diagram_judge.score(ev, prd, text)}
    if base["has_ref"]:
        gt = parse(ref_path.read_text(errors="ignore"))
        align = ev.align(prd, gt["leafnodes"] or gt["nodes"], pred["leafnodes"] or pred["nodes"])
        row.update(metrics(project, gt, pred, align))
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", choices=tuple(BENCHES), default="student")
    parser.add_argument("--project", help="Comma-separated projects (smoke test); writes scores_subset.csv")
    parser.add_argument("--model", help="Comma-separated model keys; default: all")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--rubric", choices=("full", "archi-scope"), default="full",
                        help="archi-scope: judge only ARCHI's scope (no penalty for missing actors, UIs, gateways, ...)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    bench = BENCHES[args.dataset]
    projects = [p.strip() for p in args.project.split(",")] if args.project else list_projects(bench)
    models = [m.strip() for m in args.model.split(",")] if args.model else list(bench.models)
    ev = Evaluator(bench.out)
    logger.info("judge model: %s | %d models x %d systems x %d projects",
                ev.model, len(models), len(SYSTEMS), len(projects))
    jobs = [(m, s, p) for m in models for s in SYSTEMS for p in projects
            if bench.models[m][SYSTEMS.index(s)] is not None]

    def run(job: tuple[str, str, str]) -> dict:
        try:
            return score_one(ev, bench, *job, archi_scope=args.rubric == "archi-scope")
        except Exception as e:  # one failed judge call must not sink the batch; it is recorded
            logger.error("%s/%s/%s failed: %s", *job, e)
            return {"model": job[0], "system": job[1], "project": job[2], "valid": None, "error": str(e)[:200]}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run, jobs))
    suffix = "_archi_scope" if args.rubric == "archi-scope" else ""
    name = f"scores{suffix}{'_subset' if args.project or args.model else ''}.csv"
    write_csv(bench.out / name, rows)
    failed = sum(r.get("valid") is None for r in rows)
    logger.info("scored %d jobs (%d failed) -> %s", len(rows), failed, bench.out / name)


if __name__ == "__main__":
    main()
