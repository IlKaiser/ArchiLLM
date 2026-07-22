# ADR Generation & DeepSeek Judge Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the PENTION deliverable into the archi dataset format, generate one Architecture Decision Record per pattern in the existing pattern catalogue, score those ADRs 1-5 with a DeepSeek-powered LLM judge, and surface both in the Streamlit UI.

**Architecture:** Four independent, sequentially-buildable Python modules — a one-off dataset script, an "agent" module that does one templated `litellm` completion per pattern, an `Evaluation/`-style judge module using an OpenAI-compatible client pointed at DeepSeek, and a Streamlit render function appended to the existing `app.py` without touching its current logic.

**Tech Stack:** `pypdf`, `openpyxl`, `litellm`, `openai`, `streamlit`, `pytest` — all already pinned in `environment.yml`. No new dependencies.

## Global Constraints

- No new dependencies beyond `pypdf`, `openpyxl`, `litellm`, `openai`, `streamlit`, `pytest` (all already in `environment.yml`).
- ADR generation and PENTION extraction use plain `litellm.completion()` / `openai.OpenAI` calls — no openhands `Agent`/sandboxing, since both are templated single-shot generation over static in-repo text, not file exploration.
- `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_JUDGE_MODEL` are new, dedicated env vars — kept separate from the existing `LLM_JUDGE_KEY` / `LLM_JUDGE_URL` / `JUDGE_MODEL` (which remain the diagram-evaluation judge, default gpt-4o).
- ADRs are written to `docs/adr/{NNN}-{slug}.md`, numbered in `KNOWLEDGE_BASE` source order (`src/prompt.py`).
- `app.py`'s existing diagram-pipeline code (lines 1–486 as of this plan) is not modified — only new sidebar fields and one appended function call at the end of the file.
- The PENTION deliverable PDF is marked "Sensitive (SEN)" dissemination level; its extracted text is sent to whatever provider `LLM_MODEL` points at via `litellm`. This is expected and already surfaced to the user — no additional redaction logic is required.

---

### Task 1: PENTION dataset extraction script

**Files:**
- Create: `scripts/pention_to_dataset.py`
- Test: `tests/test_pention_to_dataset.py`

**Interfaces:**
- Consumes: `dataset/pention/PENTION_Deliverable_1.1_v1.4_Revised-All copy.pdf` (27 pages, real file already in repo), `dataset/pention/PENTION_requirements_elicitation.xlsx` (sheet `Requirements List`, header row `Category, ID, Requirement, Type, Stakeholders, Title, Description, Source, Survey, Matrix`, 71 data rows, real file already in repo).
- Produces: `dataset/pention/input.txt` (not consumed by any other task in this plan).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pention_to_dataset.py`:

```python
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import pention_to_dataset as p2d

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_XLSX = REPO_ROOT / "dataset" / "pention" / "PENTION_requirements_elicitation.xlsx"


def test_extract_requirements_reads_real_xlsx():
    requirements = p2d.extract_requirements(REAL_XLSX)
    assert len(requirements) >= 70
    first = requirements[0]
    assert first["ID"] == "HLG1"
    assert first["Category"] == "High-Level Goal"
    assert "synthetic drug" in first["Requirement"].lower()


def test_format_requirements_includes_id_and_stakeholders():
    requirements = [
        {"ID": "R1", "Category": "Functional", "Requirement": "Do X", "Stakeholders": "Users"},
    ]
    text = p2d.format_requirements(requirements)
    assert "R1" in text
    assert "Functional" in text
    assert "Do X" in text
    assert "Users" in text


def test_build_prompt_embeds_pdf_and_requirements():
    requirements = [
        {"ID": "R1", "Category": "Functional", "Requirement": "Do X", "Stakeholders": "Users"},
    ]
    prompt = p2d.build_prompt("Some deliverable text.", requirements)
    assert "Some deliverable text." in prompt
    assert "Do X" in prompt
    assert "# SYSTEM DESCRIPTION:" in prompt
    assert "# USER STORIES:" in prompt


def test_generate_input_txt_calls_litellm(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "# SYSTEM DESCRIPTION:\nfoo\n\n# USER STORIES:\n1. bar"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(p2d.litellm, "completion", fake_completion)
    monkeypatch.setenv("LLM_MODEL", "test/model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    result = p2d.generate_input_txt("some prompt")

    assert result == "# SYSTEM DESCRIPTION:\nfoo\n\n# USER STORIES:\n1. bar"
    fake_completion.assert_called_once_with(
        model="test/model",
        api_key="test-key",
        messages=[{"role": "user", "content": "some prompt"}],
    )


def test_main_writes_output_file(monkeypatch, tmp_path):
    output_path = tmp_path / "input.txt"
    monkeypatch.setattr(p2d, "PDF_PATH", tmp_path / "fake.pdf")
    monkeypatch.setattr(p2d, "XLSX_PATH", tmp_path / "fake.xlsx")
    monkeypatch.setattr(p2d, "OUTPUT_PATH", output_path)
    monkeypatch.setattr(p2d, "extract_pdf_text", lambda path: "pdf text")
    monkeypatch.setattr(p2d, "extract_requirements", lambda path: [])
    monkeypatch.setattr(p2d, "generate_input_txt", lambda prompt: "GENERATED CONTENT")

    p2d.main()

    assert output_path.read_text(encoding="utf-8") == "GENERATED CONTENT"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pention_to_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts'` (or `scripts.pention_to_dataset`).

- [ ] **Step 3: Create `scripts/__init__.py` and implement `scripts/pention_to_dataset.py`**

Create empty `scripts/__init__.py` (makes `scripts` importable as a package):

```python
```

Create `scripts/pention_to_dataset.py`:

```python
"""
pention_to_dataset.py — one-off extraction of the PENTION deliverable
(PDF + requirements-elicitation xlsx) into dataset/pention/input.txt,
matching the archi dataset format used by dataset/*/input.txt.

Run: python scripts/pention_to_dataset.py
"""
from __future__ import annotations

import os
from pathlib import Path

import litellm
import openpyxl
import pypdf
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
PENTION_DIR = REPO_ROOT / "dataset" / "pention"
PDF_PATH = PENTION_DIR / "PENTION_Deliverable_1.1_v1.4_Revised-All copy.pdf"
XLSX_PATH = PENTION_DIR / "PENTION_requirements_elicitation.xlsx"
OUTPUT_PATH = PENTION_DIR / "input.txt"

MAX_PDF_CHARS = 12000

PENTION_EXTRACT_PROMPT = """
## Task
You are converting an EU research-project deliverable into the exact dataset
format used by this repository's architecture dataset.

## Source: Deliverable Text (truncated)
{pdf_text}

## Source: Requirements List
{requirements_text}

## Output Format
Produce ONLY the following, with no extra commentary:

# SYSTEM DESCRIPTION:
<2-4 paragraph summary of what the PENTION project builds and why>

# USER STORIES:
1. As a <stakeholder>, I want <requirement>, so that <goal>.
2. As a <stakeholder>, I want <requirement>, so that <goal>.
...

## Rules
- Write one user story per row in the Requirements List, in the same order.
- Use the row's Stakeholders field for "As a <stakeholder>".
- Use the row's Requirement (and Description, if present) to phrase the
  "I want ... so that ..." clause.
- Do not invent requirements not present in the Requirements List.
"""


def extract_pdf_text(pdf_path: Path, max_chars: int = MAX_PDF_CHARS) -> str:
    """Concatenate extracted text from every page, truncated to max_chars."""
    reader = pypdf.PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text[:max_chars]


def extract_requirements(xlsx_path: Path) -> list[dict]:
    """Read the 'Requirements List' sheet into a list of row dicts."""
    workbook = openpyxl.load_workbook(str(xlsx_path), data_only=True)
    sheet = workbook["Requirements List"]
    rows = list(sheet.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]
    requirements = []
    for row in rows[1:]:
        if row is None or all(cell is None for cell in row):
            continue
        entry = dict(zip(header, row))
        requirements.append(entry)
    return requirements


def format_requirements(requirements: list[dict]) -> str:
    """Render requirement rows as one line each for the LLM prompt."""
    lines = []
    for req in requirements:
        rid = req.get("ID", "")
        category = req.get("Category", "")
        text = req.get("Requirement", "")
        stakeholders = req.get("Stakeholders", "")
        lines.append(f"{rid} [{category}] {text} (stakeholders: {stakeholders})")
    return "\n".join(lines)


def build_prompt(pdf_text: str, requirements: list[dict]) -> str:
    return PENTION_EXTRACT_PROMPT.format(
        pdf_text=pdf_text,
        requirements_text=format_requirements(requirements),
    )


def generate_input_txt(prompt: str) -> str:
    model = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    api_key = os.getenv("LLM_API_KEY")
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def main() -> None:
    pdf_text = extract_pdf_text(PDF_PATH)
    requirements = extract_requirements(XLSX_PATH)
    prompt = build_prompt(pdf_text, requirements)
    content = generate_input_txt(prompt)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pention_to_dataset.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/__init__.py scripts/pention_to_dataset.py tests/test_pention_to_dataset.py
git commit -m "feat: add PENTION deliverable extraction script"
```

---

### Task 2: ADR generator agent

**Files:**
- Create: `src/adr_agent.py`
- Test: `tests/test_adr_agent.py`

**Interfaces:**
- Consumes: `KNOWLEDGE_BASE` (str constant, already exists in `src/prompt.py`).
- Produces:
  - `parse_patterns(knowledge_base: str) -> list[dict]` — each dict has keys `"name"`, `"slug"`, `"body"`.
  - `slugify(name: str) -> str`
  - `run(patterns: list[str] | None = None, output_dir: str = "docs/adr") -> list[dict]` — each returned dict has keys `"pattern"`, `"slug"`, `"path"`, `"content"`. Consumed by Task 3 (`Evaluation/adr_judge.py`, via `parse_patterns`) and Task 4 (`src/adr_frontend.py`, via `run`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_adr_agent.py`:

```python
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import adr_agent
from src.prompt import KNOWLEDGE_BASE

EXPECTED_PATTERN_NAMES = [
    "Database per service (MANDATORY for all microservices)",
    "Saga",
    "Command-side replica",
    "API Composition",
    "Command Query Responsibility Segregation (CQRS)",
    "Domain event",
    "Event sourcing",
]


def test_parse_patterns_finds_seven_patterns_in_order():
    patterns = adr_agent.parse_patterns(KNOWLEDGE_BASE)
    assert [p["name"] for p in patterns] == EXPECTED_PATTERN_NAMES


def test_parse_patterns_body_excludes_next_header():
    patterns = adr_agent.parse_patterns(KNOWLEDGE_BASE)
    saga_pattern = patterns[1]
    assert saga_pattern["name"] == "Saga"
    assert "## Pattern: Command-side replica" not in saga_pattern["body"]
    assert "How to implement transactions that span services?" in saga_pattern["body"]


def test_slugify_matches_expected_forms():
    assert adr_agent.slugify("Saga") == "saga"
    assert adr_agent.slugify(
        "Command Query Responsibility Segregation (CQRS)"
    ) == "command-query-responsibility-segregation-cqrs"
    assert adr_agent.slugify(
        "Database per service (MANDATORY for all microservices)"
    ) == "database-per-service-mandatory-for-all-microservices"


def test_build_adr_prompt_includes_pattern_body_and_number():
    pattern = {"name": "Saga", "slug": "saga", "body": "Some saga body text."}
    prompt = adr_agent.build_adr_prompt(pattern, number=2)
    assert "Some saga body text." in prompt
    assert "ADR-{number:03d}" not in prompt  # must be substituted, not literal
    assert "ADR-002" in prompt
    assert "Saga" in prompt


def test_generate_adr_calls_litellm(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "# ADR-001: Saga\n\n**Status:** Accepted"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(adr_agent.litellm, "completion", fake_completion)

    pattern = {"name": "Saga", "slug": "saga", "body": "Some saga body text."}
    result = adr_agent.generate_adr(pattern, number=1, model="test/model", api_key="test-key")

    assert result == "# ADR-001: Saga\n\n**Status:** Accepted"
    fake_completion.assert_called_once()
    call_kwargs = fake_completion.call_args.kwargs
    assert call_kwargs["model"] == "test/model"
    assert call_kwargs["api_key"] == "test-key"


def test_run_writes_numbered_files_and_returns_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adr_agent, "generate_adr", lambda pattern, number, model=None, api_key=None: f"CONTENT for {pattern['name']}"
    )

    results = adr_agent.run(patterns=["Saga"], output_dir=str(tmp_path))

    assert len(results) == 1
    assert results[0]["pattern"] == "Saga"
    assert results[0]["slug"] == "saga"
    assert results[0]["path"] == str(tmp_path / "001-saga.md")
    assert results[0]["content"] == "CONTENT for Saga"
    assert (tmp_path / "001-saga.md").read_text(encoding="utf-8") == "CONTENT for Saga"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_adr_agent.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.adr_agent'`.

- [ ] **Step 3: Implement `src/adr_agent.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_adr_agent.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add src/adr_agent.py tests/test_adr_agent.py
git commit -m "feat: add ADR generator agent for the pattern catalogue"
```

---

### Task 3: DeepSeek ADR judge

**Files:**
- Create: `Evaluation/adr_judge.py`
- Create: `Evaluation/adr_judge_prompt.md`
- Modify: `.env.template` (add 3 lines)
- Modify: `README.md` (document 3 new env vars, in the existing "Environment Variables" code block)
- Test: `tests/test_adr_judge.py`

**Interfaces:**
- Consumes: `src.adr_agent.parse_patterns` (Task 2), `src.prompt.KNOWLEDGE_BASE`.
- Produces:
  - `ADRJudge(api_key: str, base_url: str, model_name: str)` with `.score(pattern_source: str, adr_markdown: str) -> dict` and static `.extract_score(result: dict) -> int | None`.
  - `run(adr_dir: str = "docs/adr", api_key=None, base_url=None, model_name=None) -> dict` — returns `{slug: {"score", "reasoning", "missing_elements"}}`, writes `{adr_dir}/scores.json`. Consumed by Task 4 (`src/adr_frontend.py`).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_adr_judge.py`:

```python
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Evaluation"))

from Evaluation import adr_judge


def test_build_prompt_replaces_placeholders():
    judge = adr_judge.ADRJudge(api_key="x", base_url="http://example.invalid", model_name="m")
    prompt = judge._build_prompt("PATTERN SOURCE TEXT", "ADR MARKDOWN TEXT")
    assert "PATTERN SOURCE TEXT" in prompt
    assert "ADR MARKDOWN TEXT" in prompt
    assert "{{INSERT_PATTERN_HERE}}" not in prompt
    assert "{{INSERT_ADR_HERE}}" not in prompt


def test_score_parses_fenced_json():
    judge = adr_judge.ADRJudge(api_key="x", base_url="http://example.invalid", model_name="m")

    fake_message = MagicMock()
    fake_message.content = (
        '```json\n{"score": 4, "reasoning": "good", "missing_elements": ["forces"]}\n```'
    )
    fake_response = MagicMock()
    fake_response.choices = [MagicMock(message=fake_message)]
    judge.client.chat.completions.create = MagicMock(return_value=fake_response)

    result = judge.score("pattern source", "adr markdown")

    assert result == {"score": 4, "reasoning": "good", "missing_elements": ["forces"]}


def test_extract_score_returns_int_or_none():
    assert adr_judge.ADRJudge.extract_score({"score": 3}) == 3
    assert adr_judge.ADRJudge.extract_score({}) is None


def test_run_matches_adr_files_to_patterns_by_slug(monkeypatch, tmp_path):
    (tmp_path / "001-saga.md").write_text("# ADR-001: Saga", encoding="utf-8")
    (tmp_path / "002-domain-event.md").write_text("# ADR-002: Domain event", encoding="utf-8")

    fake_score_results = {
        "saga": {"score": 5, "reasoning": "complete", "missing_elements": []},
        "domain-event": {"score": 3, "reasoning": "partial", "missing_elements": ["consequences"]},
    }

    def fake_score(self, pattern_source, adr_markdown):
        if "Saga" in adr_markdown:
            return fake_score_results["saga"]
        return fake_score_results["domain-event"]

    monkeypatch.setattr(adr_judge.ADRJudge, "score", fake_score)

    scores = adr_judge.run(
        adr_dir=str(tmp_path), api_key="x", base_url="http://example.invalid", model_name="m"
    )

    assert scores["saga"]["score"] == 5
    assert scores["domain-event"]["score"] == 3
    assert scores["domain-event"]["missing_elements"] == ["consequences"]

    written = json.loads((tmp_path / "scores.json").read_text(encoding="utf-8"))
    assert written == scores
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_adr_judge.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Evaluation.adr_judge'`.

- [ ] **Step 3: Create `Evaluation/adr_judge_prompt.md`**

```markdown
# ADR Pattern-Fidelity Judge

You are scoring how faithfully a generated Architecture Decision Record
(ADR) captures the information in its source architectural-pattern
description.

## Source Pattern Description
{{INSERT_PATTERN_HERE}}

## Generated ADR
{{INSERT_ADR_HERE}}

## Task
Score the ADR from 1 to 5 on how completely and accurately it reflects the
context, problem, forces, solution, and consequences described in the
source pattern description:

- **5** — Every material piece of pattern information (context, problem,
  forces, solution, consequences/trade-offs) is present and accurately
  represented in the ADR.
- **3** — Most pattern information is present, but some forces,
  consequences, or trade-offs are missing or only partially represented.
- **1** — The ADR omits most of the pattern's information or misrepresents
  the solution/consequences.

## Output Format
Respond with ONLY a JSON object in a fenced code block:

\`\`\`json
{
  "score": <integer 1-5>,
  "reasoning": "<2-3 sentence justification>",
  "missing_elements": ["<pattern detail the ADR omitted>", "..."]
}
\`\`\`
```

- [ ] **Step 4: Implement `Evaluation/adr_judge.py`**

```python
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
        result = judge.score(pattern_source, adr_markdown)
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
```

Note: `test_run_matches_adr_files_to_patterns_by_slug` writes ADR files named
`001-saga.md` and `002-domain-event.md` — these slugs (`saga`,
`domain-event`) match exactly what `src.adr_agent.slugify` produces for
patterns `"Saga"` and `"Domain event"`, so `patterns_by_slug.get(slug)` will
find real source text for both from the real `KNOWLEDGE_BASE` (no mocking
of `parse_patterns` needed).

- [ ] **Step 5: Add new env vars to `.env.template`**

Read the current file first, then add these 3 lines at the end of
`.env.template`:

```
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_JUDGE_MODEL=deepseek-chat
```

- [ ] **Step 6: Document the new env vars in `README.md`**

In the `### Environment Variables` code block in `README.md` (currently
ending with the `# Laminar observability (optional)` section), add a new
block right after the `# LLM-as-a-judge (evaluation only)` block:

```
# ADR pattern-fidelity judge (DeepSeek, evaluation only)
DEEPSEEK_API_KEY=<your-deepseek-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_JUDGE_MODEL=deepseek-chat
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_adr_judge.py -v`
Expected: PASS (4 tests).

- [ ] **Step 8: Commit**

```bash
git add Evaluation/adr_judge.py Evaluation/adr_judge_prompt.md .env.template README.md tests/test_adr_judge.py
git commit -m "feat: add DeepSeek-powered ADR pattern-fidelity judge"
```

---

### Task 4: Streamlit frontend integration

**Files:**
- Create: `src/adr_frontend.py`
- Create: `tests/fixtures/adr_frontend_harness.py`
- Test: `tests/test_adr_frontend.py`
- Modify: `app.py` (append sidebar fields + one function call; no existing lines changed)

**Interfaces:**
- Consumes: `src.adr_agent.run` (Task 2), `Evaluation.adr_judge.run` (Task 3), `llm_model` (str, already defined at `app.py:126`).
- Produces: `render(default_llm_model: str) -> None` (called once from the bottom of `app.py`); `_list_existing_adrs`, `_load_existing_scores`, `_score_table_rows` (pure helpers, no other consumers).

- [ ] **Step 1: Write the failing tests**

Create `tests/fixtures/adr_frontend_harness.py` (a minimal script for
`streamlit.testing.v1.AppTest` to execute):

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.adr_frontend import render

render(default_llm_model="test-model")
```

Create `tests/test_adr_frontend.py`:

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

from src import adr_frontend

HARNESS_PATH = str(Path(__file__).parent / "fixtures" / "adr_frontend_harness.py")


def test_render_shows_generate_button():
    at = AppTest.from_file(HARNESS_PATH)
    at.run()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert "📜 Generate ADRs from Pattern Catalogue" in button_labels


def test_score_table_rows_formats_scores():
    rows = adr_frontend._score_table_rows(
        {"saga": {"score": 4, "reasoning": "ok"}, "domain-event": {"score": 2, "reasoning": "meh"}}
    )
    assert rows == [
        {"Pattern": "domain-event", "Score": "2/5"},
        {"Pattern": "saga", "Score": "4/5"},
    ]


def test_list_existing_adrs_reads_directory(tmp_path):
    (tmp_path / "001-saga.md").write_text("# ADR-001: Saga", encoding="utf-8")
    results = adr_frontend._list_existing_adrs(output_dir=str(tmp_path))
    assert len(results) == 1
    assert results[0]["content"] == "# ADR-001: Saga"


def test_list_existing_adrs_empty_when_dir_missing(tmp_path):
    missing_dir = tmp_path / "does-not-exist"
    results = adr_frontend._list_existing_adrs(output_dir=str(missing_dir))
    assert results == []


def test_load_existing_scores_reads_json(tmp_path):
    (tmp_path / "scores.json").write_text('{"saga": {"score": 5}}', encoding="utf-8")
    scores = adr_frontend._load_existing_scores(output_dir=str(tmp_path))
    assert scores == {"saga": {"score": 5}}


def test_load_existing_scores_empty_when_missing(tmp_path):
    scores = adr_frontend._load_existing_scores(output_dir=str(tmp_path))
    assert scores == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_adr_frontend.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.adr_frontend'`.

- [ ] **Step 3: Implement `src/adr_frontend.py`**

```python
"""
adr_frontend.py — Streamlit section for generating ADRs from the pattern
catalogue and scoring them with the DeepSeek judge. Appended to app.py
without modifying its existing diagram-pipeline logic.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from Evaluation.adr_judge import run as score_adrs
from src.adr_agent import run as generate_adrs

ADR_OUTPUT_DIR = "docs/adr"


def _list_existing_adrs(output_dir: str = ADR_OUTPUT_DIR) -> list[dict]:
    """Read any already-generated ADR markdown files off disk, sorted by filename."""
    out_dir = Path(output_dir)
    if not out_dir.exists():
        return []
    return [
        {"path": str(path), "content": path.read_text(encoding="utf-8")}
        for path in sorted(out_dir.glob("*.md"))
    ]


def _load_existing_scores(output_dir: str = ADR_OUTPUT_DIR) -> dict:
    scores_path = Path(output_dir) / "scores.json"
    if not scores_path.exists():
        return {}
    return json.loads(scores_path.read_text(encoding="utf-8"))


def _score_table_rows(scores: dict) -> list[dict]:
    """Convert the scores dict into row dicts suitable for st.dataframe."""
    return [
        {"Pattern": slug, "Score": f"{data.get('score', '—')}/5"}
        for slug, data in sorted(scores.items())
    ]


def render(default_llm_model: str) -> None:
    st.markdown("---")
    st.subheader("📜 Architecture Decision Records")
    st.caption(f"ADR generation uses LLM_MODEL: {default_llm_model}")

    regenerate = st.checkbox("🔄 Regenerate ADRs", value=False, key="chk_adr_regenerate")

    if st.button("📜 Generate ADRs from Pattern Catalogue", key="btn_gen_adr"):
        existing = _list_existing_adrs()
        if existing and not regenerate:
            st.info("Using existing ADRs. Check 'Regenerate ADRs' to force a fresh run.")
            adrs = existing
        else:
            with st.spinner("Generating ADRs from the pattern catalogue…"):
                adrs = generate_adrs()
            st.success(f"Generated {len(adrs)} ADR(s).")
        for adr in adrs:
            title = Path(adr["path"]).stem
            with st.expander(title):
                st.markdown(adr["content"])

    st.markdown("#### 🧑‍⚖️ DeepSeek Judge")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not deepseek_key:
        st.warning("Set DEEPSEEK_API_KEY in the sidebar to enable ADR scoring.")
    elif st.button("🧑‍⚖️ Score ADRs with DeepSeek", key="btn_score_adr"):
        existing_scores = _load_existing_scores()
        if existing_scores and not regenerate:
            st.info("Using existing scores. Check 'Regenerate ADRs' to force a fresh run.")
            scores = existing_scores
        else:
            with st.spinner("Scoring ADRs with DeepSeek…"):
                scores = score_adrs()
            st.success(f"Scored {len(scores)} ADR(s).")
        st.dataframe(_score_table_rows(scores), use_container_width=True)
        for slug, data in sorted(scores.items()):
            with st.expander(f"{slug} — reasoning"):
                st.write(data.get("reasoning", ""))
                missing = data.get("missing_elements", [])
                if missing:
                    st.write("Missing elements:")
                    for item in missing:
                        st.write(f"- {item}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_adr_frontend.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Wire into `app.py`**

First, read `app.py` to confirm current line numbers around the sidebar's
`## LLM Configuration` block (Task 3 in the earlier `Evaluation/adr_judge.py`
work does not touch this file, so line numbers should still match those
recorded during design: sidebar `LLM_JUDGE_*` fields end around line 130,
and the file currently ends at line 486). Then:

1. In the sidebar section, immediately after the existing line:
   ```python
   llm_judge_model = st.sidebar.text_input("JUDGE_MODEL", value=os.environ.get("JUDGE_MODEL", "gpt-5.5"), help="Model used for LLM-as-a-judge evaluation")
   ```
   insert:
   ```python

   st.sidebar.subheader("🧑‍⚖️ DeepSeek Judge (ADR scoring)")
   deepseek_api_key = st.sidebar.text_input("DEEPSEEK_API_KEY", type="password", value=os.environ.get("DEEPSEEK_API_KEY", ""))
   deepseek_base_url = st.sidebar.text_input("DEEPSEEK_BASE_URL", value=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
   deepseek_judge_model = st.sidebar.text_input("DEEPSEEK_JUDGE_MODEL", value=os.environ.get("DEEPSEEK_JUDGE_MODEL", "deepseek-chat"))
   ```

2. In the existing `if st.sidebar.button("💾 Save Keys to Environment"):` block,
   immediately after the existing line
   `os.environ["SECONDARY_LLM_API_KEY"] = secondary_llm_api_key`, insert:
   ```python
       os.environ["DEEPSEEK_API_KEY"] = deepseek_api_key
       os.environ["DEEPSEEK_BASE_URL"] = deepseek_base_url
       os.environ["DEEPSEEK_JUDGE_MODEL"] = deepseek_judge_model
   ```

3. At the very end of `app.py` (append after the final line, currently the
   closing of the `else: st.error("Output folder not found…")` block),
   append:
   ```python

   from src.adr_frontend import render as render_adr_section

   render_adr_section(default_llm_model=llm_model)
   ```

- [ ] **Step 6: Manual smoke test**

Run: `streamlit run app.py`
Expected: page loads with no exceptions; scrolling to the bottom shows the
new "📜 Architecture Decision Records" section below the existing diagram
pipeline UI; sidebar shows the new "🧑‍⚖️ DeepSeek Judge (ADR scoring)"
fields.

- [ ] **Step 7: Commit**

```bash
git add src/adr_frontend.py tests/fixtures/adr_frontend_harness.py tests/test_adr_frontend.py app.py
git commit -m "feat: surface ADR generation and DeepSeek scoring in the Streamlit UI"
```

---

## Self-Review

**Spec coverage:**
- PENTION → dataset (spec §1) → Task 1. ✅
- ADR generator agent, Google-Cloud-style chapters, one file per pattern (spec §2) → Task 2. ✅
- DeepSeek judge, 1-5 score, dedicated env vars (spec §3) → Task 3. ✅
- Frontend section appended to `app.py` without touching existing logic (spec §4) → Task 4. ✅
- Data-sensitivity note (spec "Data note") → covered in Global Constraints; no code change required, already surfaced to user in the design conversation. ✅
- "Testing / verification" section of the spec → covered by each task's test file plus Task 4 Step 6 manual smoke test. ✅

**Placeholder scan:** No `TBD`/`TODO`/"implement later" strings in any step; every code block is complete and runnable as written.

**Type consistency:** `parse_patterns` (Task 2) returns `{"name", "slug", "body"}` and is consumed identically in Task 3's `patterns_by_slug` construction. `run()` in Task 2 returns `{"pattern", "slug", "path", "content"}` and Task 4's `render()` reads `adr["path"]` / `adr["content"]` — matches. `run()` in Task 3 returns `{slug: {"score", "reasoning", "missing_elements"}}` and Task 4's `_score_table_rows` / `render()` read exactly those three keys — matches.
