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
    assert len(requirements) >= 69
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
