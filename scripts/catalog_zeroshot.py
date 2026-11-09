"""Catalog-only ablation: the zero-shot DeepSeek prompt plus ARCHIe's pattern catalog.

Same model, endpoint and decoding settings as results/deepseek_plain_baseline
(scripts/plain_prompt_baseline.py defaults); the only change is that the
prompt ends with ARCHIe's KNOWLEDGE_BASE, introduced by the sentence the
Component Generator Agent receives. No agents, no repair.

    python catalog_zeroshot.py   (from the repository root; reads dataset/student_projects)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import plain_prompt_baseline as ppb  # noqa: E402
from src.prompt import KNOWLEDGE_BASE  # noqa: E402

logger = logging.getLogger(__name__)

CATALOG_PROMPT = (
    ppb.PROMPT
    + "\n\nUse the following pattern catalogue as reference when identifying and assigning "
    "architectural patterns. Always prefer patterns from this catalogue and follow their "
    "prescribed forces, solutions, and trade-offs:\n\n"
    + KNOWLEDGE_BASE.replace("{", "{{").replace("}", "}}")
)
OUTPUT = "results/deepseek_catalog_zeroshot/student_projects"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", default=None)
    parser.add_argument("--workers", type=int, default=4)
    cli = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    ppb.load_dotenv(REPO / ".env")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is not set")
    ppb.PROMPT = CATALOG_PROMPT  # run_project formats ppb.PROMPT with the spec

    args = argparse.Namespace(
        dataset="dataset/student_projects", output=OUTPUT, model=ppb.DEFAULT_MODEL,
        base_url=ppb.DEFAULT_BASE_URL, temperature=None, max_tokens=None, disable_thinking=False,
        timeout=900.0, skip_existing=True,
    )
    dataset = REPO / args.dataset
    projects = sorted(p.name for p in dataset.iterdir() if (p / "input.txt").is_file())
    if cli.project:
        projects = [p for p in projects if p in cli.project.split(",")]
    (REPO / OUTPUT).mkdir(parents=True, exist_ok=True)
    (REPO / OUTPUT / "prompt.txt").write_text(CATALOG_PROMPT, encoding="utf-8")
    progress = ppb.Progress(REPO / "dashboard/run_progress/deepseek-catalog-zeroshot.json",
                            projects, args, f"deepseek/{args.model}")
    with ThreadPoolExecutor(max_workers=cli.workers) as pool:
        list(pool.map(lambda n: ppb.run_project(n, args, api_key, progress), projects))
    progress.finish()
    logger.info("Done: %s", progress.state["status"])


if __name__ == "__main__":
    main()
