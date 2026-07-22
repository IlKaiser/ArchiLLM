"""
adr_agent.py — generates one Architecture Decision Record per pattern
documented in src/prompt.py's KNOWLEDGE_BASE, using the chapter structure
recommended by Google Cloud's ADR guidance (authors, context/problem,
requirements, critical user journey, options considered, decision). One
templated litellm.completion() call per pattern — no openhands Agent or
sandboxing, since this is generation over static in-repo text, not file
exploration.

Run: python -m src.adr_agent
"""
from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path

import litellm

from src.prompt import KNOWLEDGE_BASE

PATTERN_HEADER_RE = re.compile(r"^## Pattern: (.+)$", re.MULTILINE)

ADR_GENERATION_PROMPT = """
## Task
Write an Architecture Decision Record (ADR) documenting the following
microservices architecture pattern, using ONLY the information given below.
Do not invent facts, benefits, or drawbacks not present in the source text.

## Pattern Name
{pattern_name}

## Source Pattern Text
{pattern_body}

## Output Format
Produce ONLY the following Markdown, with no extra commentary before or
after it:

# ADR-{number:03d}: {pattern_name}

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** {iso_date}

## Context and Problem Statement
<derived from the source text's Context/Problem/Forces>

## Requirements (Functional & Non-Functional)
<the forces / constraints the solution must satisfy, from the source text>

## Critical User Journey Impacted
<the concrete example scenario from the source text, if present, otherwise
state that no example scenario was given in the source>

## Considered Options
<alternative patterns mentioned in the source text's "Related patterns" or
"Resulting context" sections, if any>

## Decision and Rationale
<the Solution from the source text, and why it resolves the stated problem>

## Consequences
<benefits and drawbacks from the source text's "Resulting context" section>
"""


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_patterns(knowledge_base: str) -> list[dict]:
    """Split KNOWLEDGE_BASE into [{"name", "slug", "body"}, ...] in source
    order, one entry per '## Pattern: <Name>' section header.
    """
    matches = list(PATTERN_HEADER_RE.finditer(knowledge_base))
    patterns = []
    for i, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(knowledge_base)
        body = knowledge_base[start:end].strip()
        patterns.append({"name": name, "slug": slugify(name), "body": body})
    return patterns


def build_adr_prompt(pattern: dict, number: int) -> str:
    return ADR_GENERATION_PROMPT.format(
        pattern_name=pattern["name"],
        pattern_body=pattern["body"],
        number=number,
        iso_date=date.today().isoformat(),
    )


def generate_adr(
    pattern: dict,
    number: int,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    model = model or os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    api_key = api_key or os.getenv("LLM_API_KEY")
    prompt = build_adr_prompt(pattern, number)
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def run(patterns: list[str] | None = None, output_dir: str = "docs/adr") -> list[dict]:
    """Generate ADRs for the given pattern names (default: all patterns in
    KNOWLEDGE_BASE). Returns [{"pattern", "slug", "path", "content"}, ...].
    Writes each ADR to {output_dir}/{NNN}-{slug}.md, numbered 1..N over the
    (possibly filtered) pattern list.
    """
    all_patterns = parse_patterns(KNOWLEDGE_BASE)
    if patterns is not None:
        wanted = set(patterns)
        all_patterns = [p for p in all_patterns if p["name"] in wanted]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, pattern in enumerate(all_patterns, start=1):
        content = generate_adr(pattern, number=i)
        path = out_dir / f"{i:03d}-{pattern['slug']}.md"
        path.write_text(content, encoding="utf-8")
        results.append(
            {"pattern": pattern["name"], "slug": pattern["slug"], "path": str(path), "content": content}
        )
    return results


if __name__ == "__main__":
    for result in run():
        print(f"Wrote {result['path']}")
