#!/usr/bin/env python3
"""Regenerate dashboard/compare_r2a.html: ARCHI on R2ABench, checked against the
paper (arXiv:2604.06683v3, Table V), the R2ABench release tables, and our own
single-evaluator cross-evaluation (Evaluation/cross_eval.py).

Three blocks, each with an explicit comparability note:
  1. Paper vs release consistency for the 16 configurations the paper reports.
  2. Syntax validity (L0) on the paper's scale — the one metric we measure with
     the same rule as the paper, so ARCHI can be placed among its rows.
  3. Single-evaluator comparison on DeepSeek V4.1 Flash (ARCHI, plain prompt,
     R2ABench's four workflows): full view on all projects, services view on
     the frozen R2A-MS subset, paired tests and calibration vs R2ABench's L1.

Stdlib only, like compare.py. Usage: python dashboard/compare_r2a.py
"""
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = Path(__file__).resolve().parent
PAPER = DASHBOARD_DIR / "data" / "r2a_paper_table_v.json"
RELEASE = REPO / "R2ABench 2" / "Results" / "configuration_summary.csv"
CROSS = REPO / "results" / "r2a_cross_eval"
PAPER_SCALE = REPO / "results" / "r2a_paper_eval" / "paper_scale.csv"
N_PROJECTS = 68
PAPER_SCALE_COLS = {"NodeCov": "l1_node_coverage", "GenPrec": "l1_gen_precision", "EdgeF1": "l1_edge_f1",
                    "GEDAcc": "l1_structural_similarity", "Layer": "l1_boundary_accuracy",
                    "Comp": "l2_completeness_score", "Faith": "l2_faithfulness_score",
                    "Rat": "l2_architectural_rationality_score", "Trace": "l2_traceability_score",
                    "Read": "l2_readability_score", "ReqCov": "l2_requirement_coverage"}

RELEASE_COLS = {"NodeCov": "node_coverage", "GenPrec": "gen_precision", "EdgeF1": "edge_f1",
                "GEDAcc": "structural_similarity", "Layer": "layer_agreement", "Comp": "l2_completeness_score",
                "Faith": "l2_faithfulness_score", "Rat": "l2_architectural_rationality_score",
                "Trace": "l2_traceability_score", "Read": "l2_readability_score"}
L2 = ["Comp", "Faith", "Rat", "Trace", "Read"]
OUR_METRICS = ["Node_F1", "Edge_F1", "GED", "Boundary_Accuracy",
               "Score_Completeness", "Score_Accuracy", "Score_Rationality", "Score_Readability"]
CONFIG_LABELS = {"arthur": "ARCHI", "plain-prompt": "Plain prompt", "r2a-direct": "R2A Direct",
                 "r2a-metagpt-custom": "R2A MetaGPT", "r2a-mini-swe-agent": "R2A Mini-SWE",
                 "r2a-openhands": "R2A OpenHands"}


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_release() -> dict:
    rows = {}
    with open(RELEASE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["dataset"] != "pooled":
                continue
            entry = {k: _num(r[v]) for k, v in RELEASE_COLS.items()}
            entry["SV"] = _num(r["n_l0_pass"]) / _num(r["n_total"])
            entry["ReqCov"] = _num(r["req_cov"])
            entry["n_valid"] = int(_num(r["n_l0_pass"]))
            rows[(r["model_id"], r["workflow"])] = entry
    return rows


def consistency(paper: dict, release: dict) -> list[dict]:
    out = []
    for row in paper["rows"]:
        p = dict(zip(paper["columns"], row["values"]))
        r = release.get((row["model"], row["framework"]), {})
        out.append({"model": row["model"], "framework": row["framework"], "paper": p, "release": r,
                    "l2_max_abs_diff": max(abs(p[k] - r[k]) for k in L2) if r else None})
    return out


def load_cross() -> dict:
    scores = CROSS / "scores.csv"
    if not scores.is_file():
        return {}
    with open(scores, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    validity, sums = defaultdict(lambda: [0, 0]), defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["view"] == "full":
            validity[r["config"]][1] += 1
            validity[r["config"]][0] += r["valid"] == "True"
        if r["valid"] != "True":
            continue
        slices = ["all"] + (["r2a_ms"] if r["r2a_ms"] == "True" else [])
        for slice_name in slices:
            for m in OUR_METRICS:
                if _num(r.get(m)) is not None:
                    sums[(r["view"], slice_name, r["config"])][m].append(_num(r[m]))
    means = [{"view": v, "slice": s, "config": c,
              **{m: (round(sum(xs) / len(xs), 4) if xs else None) for m, xs in ms.items()},
              "n": max((len(xs) for xs in ms.values()), default=0)}
             for (v, s, c), ms in sorted(sums.items())]
    summary = json.loads((CROSS / "summary.json").read_text()) if (CROSS / "summary.json").is_file() else {}
    ms_file = CROSS / "r2a_ms_projects.csv"
    n_ms = sum(r["r2a_ms"] == "True" for r in csv.DictReader(open(ms_file))) if ms_file.is_file() else None
    return {"validity": {c: {"valid": v, "total": t} for c, (v, t) in validity.items()},
            "means": means, "paired": summary.get("paired", []),
            "calibration": summary.get("calibration", []), "n_ms": n_ms}


def load_paper_scale() -> dict:
    """Per-workflow means on R2ABench's own protocol (Evaluation/r2a_paper_eval.py).

    SV is over all 68 projects (a missing or unrenderable view is an L0 failure,
    as in the release); the other columns average valid views only. ReqCov is
    reported as a percentage, like the release's analysis tables.
    """
    if not PAPER_SCALE.is_file():
        return {}
    by_workflow = defaultdict(list)
    for r in csv.DictReader(open(PAPER_SCALE, newline="", encoding="utf-8")):
        by_workflow[r["workflow"]].append(r)
    out = {}
    for workflow, rows in by_workflow.items():
        valid = [r for r in rows if r.get("l0_valid") == "True"]
        entry = {"SV": len(valid) / N_PROJECTS, "n_valid": len(valid), "n_scored": len(rows)}
        for key, col in PAPER_SCALE_COLS.items():
            xs = [_num(r.get(col)) for r in valid if _num(r.get(col)) is not None]
            entry[key] = (sum(xs) / len(xs)) * (100 if key == "ReqCov" else 1) if xs else None
            entry[f"{key}_n"] = len(xs)
        out[workflow] = entry
    return out


def main() -> None:
    paper = json.loads(PAPER.read_text(encoding="utf-8"))
    release = load_release()
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_source": paper["source"],
        "paper_columns": paper["columns"],
        "consistency": consistency(paper, release),
        "release_flash": {wf: release.get(("deepseek-v4.1-flash", wf))
                          for wf in ("direct", "metagpt-custom", "mini-swe-agent", "openhands")},
        "cross": load_cross(),
        "paper_scale": load_paper_scale(),
        "release_all": [{"model": m, "framework": w, **v} for (m, w), v in sorted(release.items())],
        "config_labels": CONFIG_LABELS,
    }
    template = (DASHBOARD_DIR / "compare_r2a_template.html").read_text(encoding="utf-8")
    out = DASHBOARD_DIR / "compare_r2a.html"
    out.write_text(template.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
