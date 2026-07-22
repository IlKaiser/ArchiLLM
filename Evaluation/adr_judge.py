"""
adr_judge.py — LLM-as-a-judge for generated ADRs, powered by DeepSeek (or
any OpenAI-compatible endpoint). Scores each ADR 1-5 for fidelity to its
source pattern text in src/prompt.py's KNOWLEDGE_BASE. Mirrors the shape of
Evaluation/arch_scorer.py.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from openai import OpenAI

from src.adr_agent import parse_patterns
from src.prompt import KNOWLEDGE_BASE

PROMPT_TEMPLATE_PATH = Path(__file__).parent / "adr_judge_prompt.md"


class ADRJudge:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def _build_prompt(self, pattern_source: str, adr_markdown: str) -> str:
        return (
            self.prompt_template
            .replace("{{INSERT_PATTERN_HERE}}", pattern_source)
            .replace("{{INSERT_ADR_HERE}}", adr_markdown)
        )

    def score(self, pattern_source: str, adr_markdown: str) -> dict:
        prompt = self._build_prompt(pattern_source, adr_markdown)
        print(f"    -> Calling ADRJudge ({self.model_name}) for pattern-fidelity scoring...")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content or ""
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
        json_str = m.group(1) if m else raw
        return json.loads(json_str)

    @staticmethod
    def extract_score(result: dict) -> int | None:
        return result.get("score")


def run(
    adr_dir: str = "docs/adr",
    api_key: str | None = None,
    base_url: str | None = None,
    model_name: str | None = None,
) -> dict:
    """Score every ADR markdown file in adr_dir against its source pattern
    text from KNOWLEDGE_BASE (matched by slug parsed out of the filename).
    Writes {adr_dir}/scores.json: {slug: {"score", "reasoning",
    "missing_elements"}}. Returns the same dict.
    """
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    model_name = model_name or os.getenv("DEEPSEEK_JUDGE_MODEL", "deepseek-chat")

    judge = ADRJudge(api_key=api_key, base_url=base_url, model_name=model_name)
    patterns_by_slug = {p["slug"]: p["body"] for p in parse_patterns(KNOWLEDGE_BASE)}

    adr_dir_path = Path(adr_dir)
    scores: dict = {}
    for md_path in sorted(adr_dir_path.glob("*.md")):
        slug_match = re.match(r"\d+-(.+)\.md$", md_path.name)
        if not slug_match:
            continue
        slug = slug_match.group(1)
        pattern_source = patterns_by_slug.get(slug)
        if pattern_source is None:
            continue
        adr_markdown = md_path.read_text(encoding="utf-8")
        try:
            result = judge.score(pattern_source, adr_markdown)
        except Exception as e:
            scores[slug] = {"score": None, "reasoning": f"Judge call failed: {e}", "missing_elements": []}
            continue
        scores[slug] = {
            "score": ADRJudge.extract_score(result),
            "reasoning": result.get("reasoning", ""),
            "missing_elements": result.get("missing_elements", []),
        }

    scores_path = adr_dir_path / "scores.json"
    scores_path.write_text(json.dumps(scores, indent=2, ensure_ascii=False), encoding="utf-8")
    return scores


if __name__ == "__main__":
    for slug, result in run().items():
        print(f"{slug}: {result['score']}/5")
