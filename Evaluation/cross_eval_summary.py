"""Aggregate Evaluation/cross_eval.py scores into comparison tables.

Writes <out>/summary.csv and <out>/summary.md with, per configuration:
  - validity rate over all 68 projects (invalid/missing views are never averaged in),
  - mean metrics over valid views, for all projects and for the R2A-MS slice,
  - paired ARCHI-vs-configuration comparisons on jointly valid projects
    (exact/normal-approx Wilcoxon signed-rank, Holm-corrected over the family),
  - calibration: Spearman correlation between this evaluator's full-view Node/Edge
    F1 and R2ABench's own frozen node_f1/edge_f1 on the same predictions.
"""
from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr, wilcoxon

logger = logging.getLogger(__name__)

STRUCT = ["Node_F1", "Edge_F1", "GED", "Boundary_Accuracy"]
RUBRIC_PREFIX = "Score_"
REFERENCE = "arthur"
R2A_WORKFLOW = {"r2a-direct": "direct", "r2a-metagpt-custom": "metagpt-custom",
                "r2a-mini-swe-agent": "mini-swe-agent", "r2a-openhands": "openhands"}

__all__ = ["summarize"]


def _holm(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def _paired(df: pd.DataFrame, metric_cols: list[str]) -> pd.DataFrame:
    rows = []
    for (view, slice_name), part in df.groupby(["view", "slice"]):
        ref = part[part.config == REFERENCE].set_index(["subset", "project"])
        for config in sorted(set(part.config) - {REFERENCE}):
            other = part[part.config == config].set_index(["subset", "project"])
            joint = ref.index.intersection(other.index)
            for metric in metric_cols:
                a, b = ref.loc[joint, metric].astype(float), other.loc[joint, metric].astype(float)
                mask = a.notna() & b.notna()
                diff = (a - b)[mask]
                if (diff != 0).sum() < 5:
                    continue
                p = wilcoxon(a[mask], b[mask], zero_method="wilcox").pvalue
                rows.append({"view": view, "slice": slice_name, "vs": config, "metric": metric,
                             "n_pairs": int(mask.sum()), "median_diff": round(float(diff.median()), 4),
                             "p": p})
    out = pd.DataFrame(rows)
    if not out.empty:
        out["p_holm"] = _holm(out["p"].tolist())
    return out


def _calibration(df: pd.DataFrame, cohort_csv: Path) -> pd.DataFrame:
    cohort = pd.DataFrame(csv.DictReader(open(cohort_csv)))
    cohort = cohort[cohort.model_id == "deepseek-v4.1-flash"]
    full = df[(df.view == "full") & (df.slice == "all")]
    rows = []
    for config, workflow in R2A_WORKFLOW.items():
        ours = full[full.config == config].set_index(["subset", "project"])
        theirs = cohort[cohort.workflow == workflow].set_index(["dataset", "sample_id"])
        joint = ours.index.intersection(theirs.index)
        for ours_col, their_col in (("Node_F1", "node_f1"), ("Edge_F1", "edge_f1")):
            a = ours.loc[joint, ours_col].astype(float)
            b = pd.to_numeric(theirs.loc[joint, their_col], errors="coerce")
            mask = a.notna() & b.notna()
            if mask.sum() >= 5:
                rho, p = spearmanr(a[mask], b[mask])
                rows.append({"config": config, "metric": ours_col, "n": int(mask.sum()),
                             "spearman_rho": round(float(rho), 3), "p": p})
    return pd.DataFrame(rows)


def summarize(out: Path, cohort_csv: Path) -> None:
    raw = pd.read_csv(out / "scores.csv")
    rubric_cols = [c for c in raw.columns if c.startswith(RUBRIC_PREFIX)]
    metric_cols = STRUCT + rubric_cols
    full_rows = raw[raw.view == "full"]
    validity = full_rows.groupby("config")["valid"].apply(lambda v: (v == True).mean()).rename("valid_rate")  # noqa: E712

    valid = raw[raw.valid == True].copy()  # noqa: E712
    sliced = pd.concat([valid.assign(slice="all"), valid[valid.r2a_ms == True].assign(slice="r2a_ms")])  # noqa: E712
    means = (sliced.groupby(["view", "slice", "config"])[metric_cols].agg(["mean", "count"]).round(3))
    paired = _paired(sliced, metric_cols)
    calibration = _calibration(sliced, cohort_csv) if cohort_csv.is_file() else pd.DataFrame()

    means.to_csv(out / "summary.csv")
    # Machine-readable copy for dashboard/compare_r2a.py (stdlib only, no pandas).
    (out / "summary.json").write_text(json.dumps({
        "validity": validity.round(4).to_dict(),
        "paired": paired.round(6).to_dict(orient="records") if not paired.empty else [],
        "calibration": calibration.round(6).to_dict(orient="records") if not calibration.empty else [],
    }, indent=1), encoding="utf-8")
    with open(out / "summary.md", "w", encoding="utf-8") as f:
        f.write("# R2ABench cross-evaluation (single evaluator for all systems)\n\n")
        f.write("Numbers are comparable across rows of these tables only, not with the R2ABench paper.\n\n")
        f.write("## Validity (share of 68 projects with a parseable view)\n\n")
        f.write(validity.round(3).to_frame().to_markdown() + "\n\n")
        f.write("## Mean metrics over valid views\n\n" + means.to_markdown() + "\n\n")
        f.write("## ARCHI vs each configuration (paired, jointly valid projects, Holm-corrected)\n\n")
        f.write((paired.round(4).to_markdown(index=False) if not paired.empty else "_not enough pairs_") + "\n\n")
        f.write("## Calibration vs R2ABench's own L1 scores (same predictions)\n\n")
        f.write((calibration.round(4).to_markdown(index=False) if not calibration.empty else "_n/a_") + "\n")
    logger.info("wrote %s and %s", out / "summary.csv", out / "summary.md")
