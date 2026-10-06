#!/usr/bin/env python3
"""Convert an R2ABench release into ARCHI's dataset layout.

For every R2ABench project (E-R2A/<lang>/<name>, G-R2A/<sample_id>) this writes

    <out>/<E-R2A|G-R2A>/<project>/input.txt        <- checked_srs.md, verbatim
    <out>/<E-R2A|G-R2A>/<project>/ref.wsd          <- AD/ad.puml (reference view)
    <out>/<E-R2A|G-R2A>/<project>/req_final.jsonl  <- curated requirements (if present)

i.e. the student_projects format (input.txt + ref.wsd), so run_headless.py and
scripts/plain_prompt_baseline.py consume it unchanged and every system sees the
identical, unwrapped SRS. A manifest.csv with source paths and SHA-256 digests is
written next to the two subsets for provenance.

Usage:
    python scripts/r2a_to_dataset.py --r2a "R2ABench 2" --out dataset/R2A
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

SUBSETS = {"E-R2A": "*/*", "G-R2A": "s*"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert(r2a_root: Path, out_root: Path) -> list[dict]:
    """Copy every complete R2ABench project into out_root; return manifest rows."""
    rows = []
    for subset, pattern in SUBSETS.items():
        for project_dir in sorted((r2a_root / "Dataset" / subset).glob(pattern)):
            if not project_dir.is_dir():
                continue
            srs, ref = project_dir / "checked_srs.md", project_dir / "AD" / "ad.puml"
            if not (srs.is_file() and ref.is_file()):
                logger.warning("skipping incomplete project %s", project_dir)
                continue
            target = out_root / subset / project_dir.name
            target.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(srs, target / "input.txt")
            shutil.copyfile(ref, target / "ref.wsd")
            reqs = project_dir / "req_final.jsonl"
            if reqs.is_file():
                shutil.copyfile(reqs, target / "req_final.jsonl")
            rows.append({
                "subset": subset,
                "project": project_dir.name,
                "source_dir": str(project_dir.relative_to(r2a_root)),
                "srs_sha256": sha256(srs),
                "ref_sha256": sha256(ref),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--r2a", default="R2ABench 2", help="R2ABench release root")
    parser.add_argument("--out", default="dataset/R2A", help="Output dataset root")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    out_root = Path(args.out)
    rows = convert(Path(args.r2a), out_root)
    with open(out_root / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    by_subset = {s: sum(r["subset"] == s for r in rows) for s in SUBSETS}
    logger.info("wrote %d projects %s to %s", len(rows), by_subset, out_root)


if __name__ == "__main__":
    main()
