"""Service identification of every LLM in R2ABench's release, on the service-based projects.

Table II of the paper compares ARCHI with R2ABench's released settings run with
DeepSeek V4.1 Flash. The release also ships the same four settings (direct,
MetaGPT, mini-SWE-agent, OpenHands) for GPT-5, Claude Sonnet 4.6, DeepSeek V3.2
and Qwen3-Coder. This script scores all of them on the 17 service-based projects
with exactly the evaluator, judge and cache of Evaluation/cross_eval.py:

  svc_f1          node F1 between the nodes labelled as services (services view);
  svc_share       share of generated leaf nodes labelled as services;
  ref_svc_recall  share of the reference services matched by ANY generated node
                  in the full-view alignment (as in scripts/r2a_service_audit.py
                  of the paper repository).

A missing or non-rendering view counts as invalid.

    uv run --no-project --with openai --with networkx --with pandas \\
        --with python-dotenv python Evaluation/r2a_models_eval.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cross_eval as ce

logger = logging.getLogger(__name__)
WORKFLOWS = ("direct", "metagpt-custom", "mini-swe-agent", "openhands")
MODELS = ("gpt-5", "claude-sonnet-4-6", "deepseek-v3.2", "qwen3-coder-480b-a35b-instruct",
          "deepseek-v4.1-flash")
OUTPUT = "R2ABench 2/Output/{r2a_subset}/{workflow}/{model}/{project}/predicted.puml"


def _bare(node: str) -> str:
    """Comparable node path (same normalisation as r2a_service_audit.py)."""
    node = node.removeprefix("Global::")
    return " ".join(node.replace("\\n", " ").replace("\n", " ").split()).lower()


def score_one(ev: ce.Evaluator, dataset: Path, workflow: str, model: str,
              subset: str, project: str) -> dict:
    """One released view on one service-based project."""
    row = {"workflow": workflow, "model": model, "subset": subset, "project": project}
    path = ce.REPO / OUTPUT.format(r2a_subset=ce.SUBSETS[subset], workflow=workflow,
                                   model=model, project=project)
    text = path.read_text(errors="ignore") if path.is_file() else ""
    pred = ce.parse(text) if "@startuml" in text else {"nodes": []}
    if not pred.get("nodes") or not ev.renders(text):
        return {**row, "valid": False, "missing": not text}
    proj = dataset / subset / project
    prd = (proj / "input.txt").read_text(encoding="utf-8")
    gt = ce.parse((proj / "ref.wsd").read_text(errors="ignore"))
    gt_roles, pred_roles = ev.roles(gt["nodes"]), ev.roles(pred["nodes"])
    # Services view, exactly as cross_eval.score_one.
    gt_s, pred_s = ce.services_view(gt, gt_roles), ce.services_view(pred, pred_roles)
    align_s = ev.align(prd, gt_s["nodes"], pred_s["nodes"]) if pred_s["nodes"] else \
        {"matched_pairs": [], "unmatched_gt_nodes": gt_s["nodes"], "unmatched_predicted_nodes": []}
    svc = ce.metrics(project, gt_s, pred_s, align_s)
    # Any-node recall of the reference services, from the full-view alignment.
    ref_services = {_bare(n) for n in gt["nodes"] if gt_roles.get(n) == "service"}
    leaves = pred["leafnodes"] or pred["nodes"]
    align = ev.align(prd, gt["leafnodes"] or gt["nodes"], leaves)
    matched = {s for pair in align.get("matched_pairs", []) for g in pair.get("gt_nodes", [])
               for s in ref_services if _bare(g) == s or _bare(g).startswith(f"{s}::")}
    roles = collections.Counter(pred_roles.get(n, "other") for n in leaves)
    return {**row, "valid": True, "leaves": len(leaves), "pred_services": len(pred_s["nodes"]),
            "svc_share": roles["service"] / len(leaves), "svc_f1": svc["Node_F1"],
            "svc_edge_f1": svc["Edge_F1"], "ref_services": len(ref_services),
            "ref_svc_recall": len(matched) / len(ref_services) if ref_services else ""}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=ce.REPO / "dataset" / "R2A")
    parser.add_argument("--out", type=Path, default=ce.REPO / "results" / "r2a_cross_eval")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with open(args.out / "r2a_ms_projects.csv") as f:
        ms = sorted((r["subset"], r["project"]) for r in csv.DictReader(f) if r["r2a_ms"] == "True")
    ev = ce.Evaluator(args.out)
    logger.info("judge model: %s; %d service-based projects", ev.model, len(ms))
    jobs = [(w, m, s, p) for m in MODELS for w in WORKFLOWS for s, p in ms]

    def run(job: tuple[str, str, str, str]) -> dict:
        try:
            return score_one(ev, args.dataset, *job)
        except Exception as e:  # noqa: BLE001 - recorded, so one failed call does not sink the batch
            logger.error("%s failed: %s", job, e)
            return {"workflow": job[0], "model": job[1], "subset": job[2], "project": job[3],
                    "valid": None, "error": str(e)[:200]}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(run, jobs))
    ce.write_csv(args.out / "r2a_models.csv", rows)
    logger.info("wrote %d rows to %s", len(rows), args.out / "r2a_models.csv")


if __name__ == "__main__":
    main()
