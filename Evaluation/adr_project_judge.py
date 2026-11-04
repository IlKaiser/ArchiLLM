"""LLM-as-a-judge for the per-project ADRs that ARCHI writes.

Evaluation/adr_judge.py scores the generic catalogue ADRs in docs/adr against
the knowledge base. This module scores the ADRs ARCHI writes for each project,
against that project's specification, its architecture.json and, when the ADR
instantiates a catalogue pattern, the pattern's knowledge-base text. Every ADR
gets five 1-5 scores (see PROMPT) and a list of unsupported claims.

Responses are cached through cross_eval.Evaluator, like every other judge call.

    uv run --no-project --with openai --with python-dotenv --with networkx \\
        --with pandas python Evaluation/adr_project_judge.py
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cross_eval import Evaluator

from src.adr_agent import parse_patterns
from src.prompt import KNOWLEDGE_BASE

logger = logging.getLogger(__name__)
KB = {p["slug"]: p for p in parse_patterns(KNOWLEDGE_BASE)}
# ADR heading suffix "(<type>)" -> knowledge-base slug; decomposition and
# aggregate ADRs instantiate no catalogue pattern.
TYPE_TO_SLUG = {
    "database per service": "database-per-service-mandatory-for-all-microservices",
    "saga": "saga",
    "api composition": "api-composition",
    "cqrs": "command-query-responsibility-segregation-cqrs",
    "domain event": "domain-event",
    "event sourcing": "event-sourcing",
    "command-side replica": "command-side-replica",
}
DIMENSIONS = ("grounding", "consistency", "fidelity", "alternatives", "justification")

PROMPT = """You are a senior software architect reviewing an Architecture Decision Record (ADR)
written by an automated assistant for one project. Judge only from the material below.

## Project specification
{spec}

## Project architecture (architecture.json, the design the ADR belongs to)
```json
{architecture}
```

## Catalogue pattern the ADR instantiates
{pattern}

## ADR under review
{adr}

Rate the ADR on each dimension from 1 to 5 (5 = fully meets it, 3 = partly, with
clear gaps, 1 = fails it):

- grounding: the context and requirements reflect the specification, and every
  cited user story actually supports the statement it is attached to.
- consistency: the decision agrees with the architecture: same services, data
  stores, dependencies and pattern application; it invents nothing that the
  architecture lacks or contradicts.
- fidelity: the solution and its consequences are faithful to the catalogue
  pattern and adapted to this project rather than copied. Use null if no
  catalogue pattern is given.
- alternatives: the considered options are plausible for this project and are
  rejected for project-specific reasons; the drawbacks are concrete and honest.
- justification: the rationale shows why this project needs this decision,
  rather than restating the pattern's generic benefits. A decision the
  specification does not call for scores low however well it is written.

Also list every claim in the ADR that the specification or the architecture
does not support or that contradicts them (including wrong user-story citations).

Answer ONLY with JSON:
{{"grounding": <1-5>, "consistency": <1-5>, "fidelity": <1-5 or null>,
  "alternatives": <1-5>, "justification": <1-5>,
  "unsupported_claims": ["<claim>", "..."],
  "reasoning": "<2-4 sentences>"}}"""


@dataclass(frozen=True)
class AdrItem:
    """One per-project ADR to score."""

    project: str
    path: Path
    adr_type: str


def _adr_type(text: str) -> str:
    heading = text.strip().splitlines()[0]
    if "decomposition" in heading.lower() and not re.search(r"\(([^()]*)\)\s*$", heading):
        return "decomposition"
    match = re.search(r"\(([^()]*)\)\s*$", heading)
    return match.group(1).strip().lower() if match else "other"


def collect(results: Path) -> tuple[list[AdrItem], list[Path]]:
    """Non-empty ADRs under results/<project>/adr, and the empty files."""
    items, empty = [], []
    for path in sorted(results.glob("*/adr/[0-9]*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            empty.append(path)
            continue
        items.append(AdrItem(project=path.parent.parent.name, path=path, adr_type=_adr_type(text)))
    return items, empty


def _parse_json(raw: str) -> dict:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    return json.loads(match.group(1) if match else raw)


def judge(ev: Evaluator, item: AdrItem, dataset: Path, results: Path) -> dict:
    """Judge one ADR; returns a flat row for the scores CSV."""
    spec = (dataset / item.project / "input.txt").read_text(encoding="utf-8")
    architecture = (results / item.project / "architecture.json").read_text(encoding="utf-8")
    slug = TYPE_TO_SLUG.get(item.adr_type)
    pattern = f"### {KB[slug]['name']}\n{KB[slug]['body']}" if slug else "None."
    adr = item.path.read_text(encoding="utf-8")
    prompt = PROMPT.format(spec=spec, architecture=architecture, pattern=pattern, adr=adr)

    def compute() -> dict:
        resp = ev.client.chat.completions.create(
            model=ev.model, response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}])
        return _parse_json(resp.choices[0].message.content or "{}")

    verdict = ev._cached("adr_project", prompt, compute)
    row = {"project": item.project, "adr": item.path.name, "type": item.adr_type}
    for dim in DIMENSIONS:
        value = verdict.get(dim)
        row[dim] = "" if value is None or (dim == "fidelity" and not slug) else value
    row["unsupported"] = len(verdict.get("unsupported_claims") or [])
    row["unsupported_claims"] = json.dumps(verdict.get("unsupported_claims") or [], ensure_ascii=False)
    row["reasoning"] = verdict.get("reasoning", "")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, default=REPO / "results" / "student_projects")
    parser.add_argument("--dataset", type=Path, default=REPO / "dataset" / "student_projects")
    parser.add_argument("--out", type=Path, default=REPO / "results" / "adr_judge")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    items, empty = collect(args.results)
    logger.info("%d ADRs to judge; %d empty files skipped: %s",
                len(items), len(empty), [str(p.relative_to(args.results)) for p in empty])
    ev = Evaluator(args.out)
    logger.info("judge model: %s", ev.model)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda it: judge(ev, it, args.dataset, args.results), items))
    args.out.mkdir(parents=True, exist_ok=True)
    out = args.out / "scores.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    logger.info("wrote %d rows to %s", len(rows), out)


if __name__ == "__main__":
    main()
