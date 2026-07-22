# ADR Generation & DeepSeek Judge Pipeline — Design

## Summary

Three additions to ARTHUR (ARCHILLMv2):

1. Extract the PENTION deliverable (PDF + requirements-elicitation xlsx) into a
   `dataset/pention/input.txt` matching the existing archi dataset format
   (`# SYSTEM DESCRIPTION:` / `# USER STORIES:`).
2. A new "agent" (`src/adr_agent.py`) that generates one Architecture Decision
   Record per architectural pattern already documented in `src/prompt.py`'s
   `KNOWLEDGE_BASE`, using the chapter structure described by Google Cloud's
   ADR guidance.
3. An LLM-as-a-judge (`Evaluation/adr_judge.py`), powered by DeepSeek, that
   scores each generated ADR 1–5 for fidelity to its source pattern text.
4. A Streamlit section (`src/adr_frontend.py`) exposing (2) and (3) as buttons
   with results rendered inline, appended to the existing `app.py` page.

## Data note

`dataset/pention/PENTION_Deliverable_1.1_v1.4_Revised-All copy.pdf` is marked
**Dissemination level: Sensitive (SEN)** in its own front matter. Step 1 sends
extracted text from this file to whichever provider `LLM_MODEL` points at (via
`litellm`). This is the user's own configured provider for their own project
data; no further redistribution happens. Flagged here for the record.

## 1. `scripts/pention_to_dataset.py`

Standalone script (same tier as `repo_to_puml.py` — not part of `src/`, no
CLI framework needed beyond `argparse`-free `if __name__ == "__main__"`).

- Read all pages of the PENTION deliverable PDF via `pypdf.PdfReader`,
  concatenate `page.extract_text()`.
- Read the `Requirements List` sheet of
  `dataset/pention/PENTION_requirements_elicitation.xlsx` via `openpyxl`
  (columns: Category, ID, Requirement, Type, Stakeholders, Title,
  Description, Source, Survey, Matrix). Build one line per row:
  `{ID} [{Category}] {Requirement} (stakeholders: {Stakeholders})`.
- Compose a single prompt (new `PENTION_EXTRACT_PROMPT` constant local to the
  script — this is a one-off dataset-prep tool, not a reusable pipeline
  prompt, so it does not belong in `src/prompt.py`) instructing the model to
  emit exactly:
  ```
  # SYSTEM DESCRIPTION:
  <2-4 paragraph summary of the PENTION project>

  # USER STORIES:
  1. As a <stakeholder>, I want <requirement>, so that <goal>.
  2. ...
  ```
  grounded in the extracted PDF text (truncated to a safe context budget) and
  the full requirements table.
- Call `litellm.completion(model=os.getenv("LLM_MODEL"), api_key=os.getenv("LLM_API_KEY"), messages=[...])`.
- Write the response content to `dataset/pention/input.txt`.
- No CLI flags — running the script with no arguments does the whole thing;
  paths are resolved relative to the repo root (`Path(__file__).resolve().parents[1]`).

## 2. `src/adr_agent.py`

### Pattern parsing

`KNOWLEDGE_BASE` in `src/prompt.py` is one big string with `## Pattern: <Name>`
section headers. Add a small parser (lives in `adr_agent.py`, not
`prompt.py`, to keep `prompt.py` focused on prompt text):

```python
def parse_patterns(knowledge_base: str) -> list[dict]:
    """Split KNOWLEDGE_BASE into [{name, slug, body}, ...] in source order."""
```

Splits on the regex `r"^## Pattern: (.+)$"` (multiline), one entry per match,
`body` = everything up to the next `## Pattern:` header or end of string.
7 entries expected from the current knowledge base.

### ADR prompt template

New constant `ADR_GENERATION_PROMPT` in `adr_agent.py` (co-located with its
only consumer). Google Cloud's ADR documentation prescribes no fixed section
headers — it lists chapters an ADR should cover (authors, context/problem,
requirements, critical user journey, options considered, decision) — so the
template below turns those into concrete headers:

```
# ADR-{number:03d}: {title}

**Status:** Accepted
**Authors:** ArchiLLM ADR Generator (LLM-assisted from pattern catalogue)
**Date:** {iso_date}

## Context and Problem Statement
## Requirements (Functional & Non-Functional)
## Critical User Journey Impacted
## Considered Options
## Decision and Rationale
## Consequences
```

The prompt passes the pattern's raw `body` text as grounding and instructs
the model not to invent facts beyond it — every section must be traceable to
the source pattern text.

### Generation call

Same lightweight approach as (1): one `litellm.completion()` call per
pattern (no openhands Agent — this is templated text generation from static
in-repo content, not file exploration or tool use).

### Public API

```python
def run(patterns: list[str] | None = None, output_dir: str = "docs/adr") -> list[dict]:
    """Generate ADRs for the given pattern names (default: all 7).
    Returns [{"pattern": str, "slug": str, "path": str, "content": str}, ...].
    Writes each ADR to {output_dir}/{NNN}-{slug}.md.
    """
```

`if __name__ == "__main__":` calls `run()` with no args to regenerate all 7.

### Output

`docs/adr/001-database-per-service.md` … `007-event-sourcing.md`, numbered in
`KNOWLEDGE_BASE` source order (Database per service, Saga, Command-side
replica, API Composition, CQRS, Domain event, Event sourcing).

## 3. `Evaluation/adr_judge.py` + `Evaluation/adr_judge_prompt.md`

Mirrors the existing `Evaluation/arch_scorer.py` shape exactly (same file
already demonstrates the "OpenAI-compatible client + prompt.md template +
```json fenced response" pattern for this codebase):

```python
class ADRJudge:
    def __init__(self, api_key: str, base_url: str, model_name: str): ...
    def score(self, pattern_source: str, adr_markdown: str) -> dict:
        """Returns {"score": 1-5, "reasoning": str, "missing_elements": [str, ...]}"""
    @staticmethod
    def extract_score(result: dict) -> int | None: ...
```

`adr_judge_prompt.md` is a rubric prompt (`{{INSERT_PATTERN_HERE}}` /
`{{INSERT_ADR_HERE}}` placeholders, following `arch_scorer`'s
`{{INSERT_PRD_HERE}}` / `{{INSERT_CODE_HERE}}` convention) asking DeepSeek to
rate 1–5 how faithfully the ADR captures the pattern's forces, solution, and
consequences, plus list any pattern information the ADR omitted.

### New env vars (`.env.template`, README)

```
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_JUDGE_MODEL=deepseek-chat
```

Kept separate from `LLM_JUDGE_KEY`/`LLM_JUDGE_URL`/`JUDGE_MODEL`, which
remain dedicated to the existing diagram-evaluation judge (gpt-4o by
default) — no collision between the two judges.

### Public API

```python
def run(adr_dir: str = "docs/adr", api_key=None, base_url=None, model_name=None) -> dict:
    """Score every ADR in adr_dir against its source pattern from KNOWLEDGE_BASE.
    Writes {adr_dir}/scores.json: {slug: {"score": int, "reasoning": str, "missing_elements": [...]}}.
    Returns the same dict.
    """
```

## 4. Frontend — `src/adr_frontend.py`, wired from `app.py`

- New module exposing `render(default_llm_model: str)` — a Streamlit
  function, imported and called once from the bottom of `app.py` (after the
  existing download button), so the existing diagram-pipeline code path is
  untouched.
- Sidebar: 3 new text inputs under a "🧑‍⚖️ DeepSeek Judge" subheader
  (`DEEPSEEK_API_KEY` password field, `DEEPSEEK_BASE_URL`,
  `DEEPSEEK_JUDGE_MODEL`) — added in `app.py` next to the existing
  `LLM_JUDGE_*` sidebar fields.
- Main area, below a `st.markdown("---")` divider:
  - "📜 Generate ADRs from Pattern Catalogue" button → calls
    `src.adr_agent.run()`, then renders each returned ADR in its own
    `st.expander(pattern_name)` with `st.markdown(content)`.
  - "🧑‍⚖️ Score ADRs with DeepSeek" button (disabled with a warning if
    `DEEPSEEK_API_KEY` is blank) → calls `Evaluation.adr_judge.run()`,
    renders a small table (pattern | score /5) plus per-pattern
    reasoning/missing-elements in expanders.
  - Both buttons are idempotent re-reads if `docs/adr/*.md` /
    `docs/adr/scores.json` already exist (skip regeneration unless a
    "🔄 Regenerate" checkbox is ticked) — mirrors the existing
    "Override existing outputs" pattern already used for the diagram
    pipeline.

## Testing / verification

- `python scripts/pention_to_dataset.py` → inspect `dataset/pention/input.txt`
  manually for format compliance (matches `# SYSTEM DESCRIPTION:` /
  `# USER STORIES:` shape of an existing project).
- `python -m src.adr_agent` → confirm 7 files land in `docs/adr/`, each
  parses as valid Markdown with all 6 required headers present.
- `python -m Evaluation.adr_judge` (small `__main__` block) → confirm
  `docs/adr/scores.json` has 7 entries, each score in `1..5`.
- Manual Streamlit smoke test: `streamlit run app.py`, click both new
  buttons, confirm no exceptions and results render.

## Out of scope

- No changes to the existing diagram-generation pipeline, EffortRouter, or
  structural metrics code.
- No new dependency additions beyond what's already in `environment.yml`
  (`pypdf`, `openpyxl`, `litellm`, `openai`, `streamlit` are all already
  present).
- DeepSeek judge only scores ADRs against the pattern catalogue — it does
  not re-score diagrams or architectures (that remains `arch_scorer.py`'s
  job).
