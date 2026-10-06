#!/usr/bin/env python3
"""Score new systems on R2ABench's own published scale (paper protocol).

Uses R2ABench's released evaluation code unchanged (``R2ABench 2/evaluation_script``):
L0 renderer gate, L1 ``l1-correspondence-v2`` alignment with gpt-5.4-mini plus the
offline hierarchy-aware edge step that produced ``Results/l1.csv``, the frozen L2
rubric and curated ReqCov. This module only stages inputs and drives it.

Commands:
  verify   recompute L1 for every released prediction from its frozen alignment and
           check the result equals Results/l1.csv (offline; validates this driver).
  stage    copy our predictions into an R2ABench-style Output tree.
  score    run R2ABench's batch evaluator (L0, L1 judge, L2, ReqCov) on the staged
           tree, then apply the hierarchy-aware L1 step; writes paper_scale.csv.

    python Evaluation/r2a_paper_eval.py verify
    python Evaluation/r2a_paper_eval.py stage
    PLANTUML_JAR=... python Evaluation/r2a_paper_eval.py score
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

REPO = Path(__file__).resolve().parent.parent
R2A = REPO / "R2ABench 2"
OUT = REPO / "results" / "r2a_paper_eval"
MODEL_ID = "deepseek-v4.1-flash"
JUDGE = "gpt-5.4-mini"
# Fixed proxy port: R2ABench's L2 resume check hashes the judge base URL, so a
# random port made every resumed run look like changed inputs and re-judge L2.
PROXY_PORT = 18765
SUBSET_OUT = {"E-R2A": "E-R2A", "G-R2A": "G-R2A-52"}
L1_KEYS = ("l1_node_coverage", "l1_gen_precision", "l1_edge_f1", "l1_boundary_accuracy", "l1_structural_similarity")
OURS = {  # workflow name in the staged tree -> our prediction path template
    "arthur": "results/arthur_r2a/deepseek_flash/{subset}/{project}/component_diagram.puml",
    "plain-prompt": "results/plain_r2a/deepseek_flash/{subset}/{project}/component_diagram.puml",
    # Control: R2ABench's own released DeepSeek V4.1 Flash "direct" views, judged
    # afresh here. Their distance from the released scores is the run-to-run judge
    # variance that bounds how precisely the rows above compare with the release.
    "r2a-direct-rejudged": "R2ABench 2/Output/{subset_out}/direct/deepseek-v4.1-flash/{project}/predicted.puml",
}
SCORE_COLS = ("l0_valid", "l1_status", *L1_KEYS, "l2_completeness_score", "l2_faithfulness_score",
              "l2_architectural_rationality_score", "l2_traceability_score", "l2_readability_score",
              "l2_requirement_coverage", "l2_requirement_coverage_status", "l2_status")

sys.path.insert(0, str(R2A))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from openai_compat_proxy import start_proxy  # noqa: E402
from evaluation_script.l1_hierarchy import evaluate_hierarchy  # noqa: E402
from evaluation_script.plantuml_parser import PlantUMLParser  # noqa: E402
from evaluation_script.l2_semantic import L2JudgeConfig, _chat_completion  # noqa: E402
from evaluation_script.reqcov import (  # noqa: E402
    build_reqcov_prompt, load_curated_requirements, validate_reqcov_assessments)
from evaluation_script.reqcov_citations import (  # noqa: E402
    LINE_CITATION_FORMAT, decode_assessments, line_citation_prompt)


def hierarchy_metrics(ref_path: Path, pred_path: Path, alignment_path: Path) -> dict:
    parser = PlantUMLParser()
    gt = parser.parse(ref_path.read_text(encoding="utf-8"))
    pred = parser.parse(pred_path.read_text(encoding="utf-8"))
    alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
    values, _ = evaluate_hierarchy(gt, pred, alignment)
    return values


def _float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def verify() -> None:
    """Recompute released L1 from frozen alignments; report exact-match rate."""
    rows = [r for r in csv.DictReader(open(R2A / "Results" / "l1.csv", encoding="utf-8")) if r.get("alignment_path")]
    matched = mismatched = failed = 0
    for r in rows:
        try:
            ours = hierarchy_metrics(R2A / r["ref_path"], R2A / (r["evaluated_prediction_path"] or r["pred_path"]),
                                     R2A / r["alignment_path"])
        except (OSError, ValueError, KeyError) as e:
            failed += 1
            logger.warning("%s: %s", r["id"], e)
            continue
        same = all((_float(r[k]) is None and ours.get(k) is None) or
                   (_float(r[k]) is not None and ours.get(k) is not None and abs(_float(r[k]) - ours[k]) < 1e-4)
                   for k in L1_KEYS)
        matched += same
        mismatched += not same
        if not same and mismatched <= 5:
            logger.warning("mismatch %s: %s", r["id"], {k: (r[k], ours.get(k)) for k in L1_KEYS})
    logger.info("verify: %d rows, %d exact, %d mismatched, %d failed", len(rows), matched, mismatched, failed)


def stage(dataset: Path) -> Path:
    """Copy our predictions into Output/<subset>/<workflow>/<model>/<project>/predicted.puml."""
    root = OUT / "Output"
    n = 0
    for workflow, template in OURS.items():
        for subset, subset_out in SUBSET_OUT.items():
            for project_dir in sorted((dataset / subset).iterdir()):
                src = REPO / template.format(subset=subset, subset_out=subset_out, project=project_dir.name)
                dst = root / subset_out / workflow / MODEL_ID / project_dir.name / "predicted.puml"
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_file():
                    shutil.copyfile(src, dst)
                    n += 1
                elif dst.exists():
                    dst.unlink()
    logger.info("staged %d predictions under %s", n, root)
    return root


def _dataset_root(subset: str) -> Path:
    return R2A / "Dataset" / subset


def score(staged: Path) -> None:
    """R2ABench batch evaluator per subset, then the hierarchy-aware L1 step."""
    env = dict(os.environ)
    dotenv = dict(l.split("=", 1) for l in (REPO / ".env").read_text().splitlines()
                  if "=" in l and not l.lstrip().startswith("#"))
    env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY") or dotenv.get("LLM_JUDGE_KEY", "").strip().strip('"')
    env.setdefault("PLANTUML_JAR", str(REPO / "tools" / "plantuml-1.2026.2.jar"))
    env["L2_DISABLE_THINKING"] = "0"  # GLM-gateway switch; the proxy strips it anyway
    upstream = dotenv.get("LLM_JUDGE_URL", "https://api.openai.com/v1").strip().strip('"')
    base_url, proxy = start_proxy(upstream, port=PROXY_PORT)
    # One R2ABench evaluator process per (subset, workflow): its judge calls are
    # sequential, and the jobs share nothing (own CSV, own alignment caches).
    jobs = []
    for subset, subset_out in SUBSET_OUT.items():
        for workflow in OURS:
            pred_dir = staged / subset_out / workflow
            if not pred_dir.is_dir():
                continue
            out_csv = OUT / f"eval_{subset}_{workflow}.csv"
            cmd = [sys.executable, "-m", "evaluation_script.evaluate",
                   "--pred", str(pred_dir), "--pred-root", str(staged / subset_out),
                   "--dataset-dir", str(_dataset_root(subset)), "--out", str(out_csv),
                   "--enable-l1-judge", "--enable-l2-judge", "--llm-model", JUDGE,
                   "--llm-base-url", base_url, "--llm-api-key-env", "OPENAI_API_KEY"]
            if out_csv.is_file():
                cmd += ["--resume-from", str(out_csv)]
            log = open(OUT / f"eval_{subset}_{workflow}.log", "w", encoding="utf-8")
            jobs.append((subset, subset_out, out_csv, subprocess.Popen(cmd, cwd=R2A, env=env, stdout=log, stderr=log)))
    logger.info("running %d R2ABench evaluator jobs in parallel", len(jobs))
    for *_, proc in jobs:
        proc.wait()
    rows = []
    for subset, subset_out, out_csv, proc in jobs:
        if proc.returncode != 0:
            logger.error("evaluator failed for %s (exit %s); see %s", out_csv.name, proc.returncode, out_csv.with_suffix(".log"))
            continue
        for r in csv.DictReader(open(out_csv, encoding="utf-8-sig")):  # R2ABench writes a BOM
            pred = staged / subset_out / r["workflow"] / r["model_id"] / r["sample_id"] / "predicted.puml"
            alignment = next(pred.parent.glob(f"judge_alignment_v2_{JUDGE}*.json"), None)
            row = {"subset": subset, "workflow": r["workflow"], "project": r["sample_id"],
                   **{k: r.get(k) for k in SCORE_COLS}}
            if r.get("l2_requirement_coverage_status") == "failed_validation":
                try:
                    row.update(reqcov_retry(
                        _dataset_sample_ref(subset, r["sample_id"]).parent.parent, pred,
                        L2JudgeConfig(enabled=True, model=JUDGE, base_url=base_url, api_key=env["OPENAI_API_KEY"])))
                except (ValueError, OSError) as e:
                    logger.warning("ReqCov fallback failed for %s/%s: %s", r["workflow"], r["sample_id"], e)
            if str(r.get("l0_valid")) == "True" and alignment:
                ref = _dataset_sample_ref(subset, r["sample_id"])
                row.update({k: v for k, v in hierarchy_metrics(ref, pred, alignment).items() if k in L1_KEYS})
                row["l1_protocol"] = "l1-hierarchy-offline-v1"
            rows.append(row)
    proxy.shutdown()
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / "paper_scale.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %s (%d rows)", OUT / "paper_scale.csv", len(rows))


REQCOV_MAX_ATTEMPTS = 4  # Results/reqcov.csv records attempts 1-4 before the line-citation fallback


def reqcov_retry(project_dir: Path, pred: Path, config: L2JudgeConfig) -> dict:
    """R2ABench's recorded ReqCov protocol after a failed evidence validation.

    The release re-asked the same verbatim-excerpt prompt (attempts 2-4 in
    Results/reqcov.csv: only 554/1128 passed on attempt 1) and, for the few that
    still failed, switched to the line-number citation override (10 rows).
    """
    items = load_curated_requirements(project_dir / "req_final.jsonl")
    puml = pred.read_text(encoding="utf-8")
    srs = (project_dir / "checked_srs.md").read_text(encoding="utf-8")
    prompt = build_reqcov_prompt(items, puml, srs)
    last_error = None
    for attempt in range(2, REQCOV_MAX_ATTEMPTS + 1):
        try:
            result = validate_reqcov_assessments(decode_assessments(_chat_completion(prompt, config), puml), items, puml)
            return {"l2_requirement_coverage": result["l2_requirement_coverage"],
                    "reqcov_attempt": attempt, "reqcov_citation_format": "verbatim-excerpts"}
        except ValueError as e:
            last_error = e
    raw = _chat_completion(line_citation_prompt(prompt, puml), config)
    result = validate_reqcov_assessments(decode_assessments(raw, puml, LINE_CITATION_FORMAT), items, puml)
    logger.info("ReqCov %s needed line citations after: %s", pred.parent.name, last_error)
    return {"l2_requirement_coverage": result["l2_requirement_coverage"],
            "reqcov_attempt": REQCOV_MAX_ATTEMPTS + 1, "reqcov_citation_format": LINE_CITATION_FORMAT}


def _dataset_sample_ref(subset: str, project: str) -> Path:
    matches = list(_dataset_root(subset).glob(f"**/{project}/AD/ad.puml"))
    if len(matches) != 1:
        raise FileNotFoundError(f"reference for {subset}/{project}: {matches}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("verify", "stage", "score"))
    parser.add_argument("--dataset", default="dataset/R2A")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.command == "verify":
        verify()
    elif args.command == "stage":
        stage(REPO / args.dataset)
    else:
        score(stage(REPO / args.dataset))


if __name__ == "__main__":
    main()
