"""
pattern_judge.py — LLM-as-a-judge for architectural pattern *application*
quality. For each pattern entry in a generated architecture.json, scores
1-5 how correctly that pattern was applied to this specific system, judged
against its canonical description in src/prompt.py's KNOWLEDGE_BASE.
Averages per-project (across that project's patterns) and per-model
(across all projects), mirroring the shape of Evaluation/adr_judge.py and
Evaluation/arch_scorer.py.

Usage: python Evaluation/pattern_judge.py --output-dir results/student_projects
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from openai import OpenAI

from src.adr_agent import parse_patterns
from src.prompt import KNOWLEDGE_BASE

PROMPT_TEMPLATE_PATH = Path(__file__).parent / "pattern_judge_prompt.md"
REPO = Path(__file__).resolve().parent.parent

# implementation_pattern strings (as written into architecture.json, e.g.
# "database per service", "cqrs") are free text from the actor model, not
# guaranteed to match a KB pattern's slug exactly — match by keyword instead.
# "aggregate" and any other implementation_pattern with no entry here has no
# canonical description to judge against and is skipped.
PATTERN_KEYWORDS = {
    "database-per-service-mandatory-for-all-microservices": ["database per service"],
    "saga": ["saga"],
    "command-side-replica": ["command-side replica", "command side replica"],
    "api-composition": ["api composition"],
    "command-query-responsibility-segregation-cqrs": ["cqrs"],
    "domain-event": ["domain event"],
    "event-sourcing": ["event sourcing"],
}


def match_kb_pattern(implementation_pattern: str, kb_patterns: list[dict]) -> dict | None:
    text = (implementation_pattern or "").lower()
    by_slug = {p["slug"]: p for p in kb_patterns}
    for slug, keywords in PATTERN_KEYWORDS.items():
        if slug in by_slug and any(kw in text for kw in keywords):
            return by_slug[slug]
    return None


class PatternJudge:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        self.prompt_template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")

    def _build_prompt(self, pattern_body: str, prd_text: str, group_name: str,
                       involved_services: list[str], explanation: str) -> str:
        return (
            self.prompt_template
            .replace("{{PATTERN_BODY}}", pattern_body)
            .replace("{{PRD_TEXT}}", prd_text)
            .replace("{{GROUP_NAME}}", group_name or "")
            .replace("{{INVOLVED_SERVICES}}", ", ".join(involved_services or []))
            .replace("{{EXPLANATION}}", explanation or "")
        )

    def score(self, pattern_body: str, prd_text: str, group_name: str,
              involved_services: list[str], explanation: str) -> dict:
        prompt = self._build_prompt(pattern_body, prd_text, group_name, involved_services, explanation)
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content or ""
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
        json_str = m.group(1) if m else raw
        return json.loads(json_str)


def score_project(judge: PatternJudge, dataset_dir: Path, output_dir: Path,
                   project: str, kb_patterns: list[dict]) -> dict:
    """Score every KB-matched pattern in one project's architecture.json.
    Returns {"project_score": float|None, "n_patterns": int, "patterns": [...]}.
    """
    arch_path = output_dir / project / "architecture.json"
    if not arch_path.exists():
        return {"project_score": None, "n_patterns": 0, "patterns": []}
    try:
        architecture = json.loads(arch_path.read_text(encoding="utf-8"))
    except Exception:
        return {"project_score": None, "n_patterns": 0, "patterns": []}

    input_path = dataset_dir / project / "input.txt"
    if not input_path.exists():
        input_path = dataset_dir / project / "requirements.txt"
    prd_text = input_path.read_text(encoding="utf-8")[:3000] if input_path.exists() else ""

    results = []
    for entry in architecture.get("patterns", []):
        kb_pattern = match_kb_pattern(entry.get("implementation_pattern", ""), kb_patterns)
        if kb_pattern is None:
            continue
        try:
            scored = judge.score(
                pattern_body=kb_pattern["body"],
                prd_text=prd_text,
                group_name=entry.get("group_name", ""),
                involved_services=entry.get("involved_microservices", []),
                explanation=entry.get("explanation", ""),
            )
            results.append({
                "kb_slug": kb_pattern["slug"],
                "group_name": entry.get("group_name"),
                "score": scored.get("score"),
                "reasoning": scored.get("reasoning"),
            })
        except Exception as e:
            results.append({
                "kb_slug": kb_pattern["slug"],
                "group_name": entry.get("group_name"),
                "score": None,
                "reasoning": f"Judge call failed: {e}",
            })

    scores = [r["score"] for r in results if r.get("score") is not None]
    project_score = sum(scores) / len(scores) if scores else None
    return {"project_score": project_score, "n_patterns": len(results), "patterns": results}


def run(
    dataset_dir: str,
    output_dir: str,
    projects: list[str] | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Score pattern application across every project in output_dir, write
    <output_dir>/<project>/pattern_scores.json per project, and return the
    aggregate {"model_score": float|None, "n_projects": int, "projects": {...}}.
    """
    api_key = api_key or os.getenv("LLM_JUDGE_KEY") or os.getenv("LLM_API_KEY")
    base_url = base_url or os.getenv("LLM_JUDGE_URL", "https://api.openai.com/v1")
    model_name = model_name or os.getenv("JUDGE_MODEL", "gpt-5.6-luna")

    judge = PatternJudge(api_key=api_key, base_url=base_url, model_name=model_name)
    kb_patterns = parse_patterns(KNOWLEDGE_BASE)

    dataset_path = Path(dataset_dir)
    output_path = Path(output_dir)
    if projects is None:
        projects = sorted(p.name for p in dataset_path.iterdir() if p.is_dir() and not p.name.startswith("."))

    per_project = {}
    for project in projects:
        print(f"[pattern-judge] scoring {project}...")
        result = score_project(judge, dataset_path, output_path, project, kb_patterns)
        per_project[project] = result
        out_path = output_path / project / "pattern_scores.json"
        if out_path.parent.exists():
            out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        score_str = f"{result['project_score']:.2f}" if result["project_score"] is not None else "n/a"
        print(f"  -> {score_str} ({result['n_patterns']} patterns)")

    project_scores = [r["project_score"] for r in per_project.values() if r["project_score"] is not None]
    model_score = sum(project_scores) / len(project_scores) if project_scores else None
    return {"model_score": model_score, "n_projects": len(project_scores), "projects": per_project}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="dataset/student_projects")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project", help="Comma-separated project name(s); default all")
    args = parser.parse_args()

    projects = [p.strip() for p in args.project.split(",")] if args.project else None
    summary = run(dataset_dir=args.dataset_dir, output_dir=args.output_dir, projects=projects)
    score_str = f"{summary['model_score']:.2f}" if summary["model_score"] is not None else "n/a"
    print(f"\nModel pattern-application score: {score_str} (across {summary['n_projects']} projects)")


if __name__ == "__main__":
    main()
