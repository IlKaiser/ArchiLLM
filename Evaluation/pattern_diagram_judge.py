"""Diagram-only pattern-application scoring, usable for any system's output.

Evaluation/pattern_judge.py scores the patterns ARCHI *claims* in its
architecture.json, which zero-shot runs do not produce. This module scores
patterns from the PlantUML diagram alone, so ARCHI and zero-shot are judged
on the same evidence:

  1. detect  for each knowledge-base pattern (given its canonical
             description), the judge decides from the diagram alone whether
             the diagram applies it, citing diagram elements;
  2. score   each detected pattern is scored 1-5 with the unchanged
             pattern_judge_prompt.md rubric, the detection's evidence taking
             the place of ARCHI's self-written explanation.

Responses are cached through cross_eval.Evaluator, like every other judge call.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pattern_judge import PatternJudge  # noqa: E402
from src.adr_agent import parse_patterns  # noqa: E402
from src.prompt import KNOWLEDGE_BASE  # noqa: E402

PRD_MAX_CHARS = 3000  # same PRD excerpt length as pattern_judge.py
KB_PATTERNS = {p["slug"]: p for p in parse_patterns(KNOWLEDGE_BASE)}

DETECT_PROMPT = """You audit a microservice architecture diagram (PlantUML) for ONE pattern.

## Pattern: {name}
{body}

## Diagram
```plantuml
{puml}
```

Does the diagram apply this pattern? Count it only if the diagram's elements
(components, databases, queues, groups, arrows, notes) show the pattern's mechanism.
A name or note that merely mentions the pattern, with nothing in the structure
realising it, does not count. Do not use any knowledge beyond the diagram.

Answer ONLY with JSON:
{{"applied": true|false,
  "group_name": "<short label for where it is applied, or empty>",
  "involved_services": ["<diagram element names>"],
  "evidence": "<1-3 sentences: which diagram elements realise (or fail to realise) the mechanism>"}}"""


def _parse_json(raw: str) -> dict:
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    return json.loads(m.group(1) if m else raw)


def detect(ev, puml: str) -> list[dict]:
    """Knowledge-base patterns the diagram applies, one judge question per pattern."""
    found = []
    for slug, pattern in KB_PATTERNS.items():
        def compute(pattern=pattern):
            prompt = DETECT_PROMPT.format(name=pattern["name"], body=pattern["body"], puml=puml)
            resp = ev.client.chat.completions.create(
                model=ev.model, response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}])
            return _parse_json(resp.choices[0].message.content or "{}")
        verdict = ev._cached("pattern_detect", json.dumps([slug, puml]), compute)
        if verdict.get("applied") is True:
            found.append({"slug": slug, **verdict})
    return found


def score(ev, prd: str, puml: str) -> dict:
    """{"Pattern_Score": mean 1-5 or None, "Pattern_Count": int, "pattern_detail": json}."""
    prd = prd[:PRD_MAX_CHARS]
    judge = PatternJudge(ev.key, ev.url, ev.model)
    results = []
    for p in detect(ev, puml):
        body = KB_PATTERNS[p["slug"]]["body"]
        args = (body, prd, p.get("group_name", ""), p.get("involved_services", []), p.get("evidence", ""))
        scored = ev._cached("pattern_score", json.dumps(args), lambda a=args: judge.score(*a))
        results.append({"slug": p["slug"], "group_name": p.get("group_name"),
                        "score": scored.get("score"), "evidence": p.get("evidence"),
                        "reasoning": scored.get("reasoning")})
    scores = [r["score"] for r in results if isinstance(r["score"], (int, float))]
    return {"Pattern_Score": sum(scores) / len(scores) if scores else None,
            "Pattern_Count": len(results),
            "pattern_detail": json.dumps(results, ensure_ascii=False)}
