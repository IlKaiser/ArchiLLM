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


def test_run_continues_after_one_judge_failure(monkeypatch, tmp_path):
    (tmp_path / "001-saga.md").write_text("# ADR-001: Saga", encoding="utf-8")
    (tmp_path / "002-domain-event.md").write_text("# ADR-002: Domain event", encoding="utf-8")

    def fake_score(self, pattern_source, adr_markdown):
        if "Saga" in adr_markdown:
            raise ValueError("malformed JSON from DeepSeek")
        return {"score": 3, "reasoning": "partial", "missing_elements": ["consequences"]}

    monkeypatch.setattr(adr_judge.ADRJudge, "score", fake_score)

    scores = adr_judge.run(
        adr_dir=str(tmp_path), api_key="x", base_url="http://example.invalid", model_name="m"
    )

    assert scores["saga"]["score"] is None
    assert "malformed JSON from DeepSeek" in scores["saga"]["reasoning"]
    assert scores["domain-event"]["score"] == 3

    written = json.loads((tmp_path / "scores.json").read_text(encoding="utf-8"))
    assert written == scores
