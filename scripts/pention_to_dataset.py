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
