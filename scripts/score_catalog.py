"""Score the catalog-only ablation with the same judge and archi-scope rubric as Table III.

Reuses Evaluation/student_cross_eval.score_one; rows are labeled system="catalog"
and written to results/student_cross_eval/scores_archi_scope_catalog.csv.
"""
from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "Evaluation"))

import student_cross_eval as sce  # noqa: E402
from cross_eval import Evaluator, write_csv  # noqa: E402

logger = logging.getLogger(__name__)
CAT_DIR = "results/deepseek_catalog_zeroshot/student_projects"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    base = sce.BENCHES["student"]
    bench = sce.Bench(base.dataset, base.ref_name, base.out, {"deepseek": (None, CAT_DIR)})
    projects = sce.list_projects(bench)
    ev = Evaluator(bench.out)
    logger.info("judge model: %s | %d projects", ev.model, len(projects))

    def run(project: str) -> dict:
        try:
            row = sce.score_one(ev, bench, "deepseek", "zeroshot", project, archi_scope=True)
        except Exception as e:  # record the failure, keep the batch going
            logger.error("%s failed: %s", project, e)
            row = {"model": "deepseek", "project": project, "valid": None, "error": str(e)[:200]}
        return {**row, "system": "catalog"}

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(run, projects))
    out = bench.out / "scores_archi_scope_catalog.csv"
    write_csv(out, rows)
    logger.info("scored %d (%d failed) -> %s", len(rows), sum(r.get("valid") is None for r in rows), out)


if __name__ == "__main__":
    main()
