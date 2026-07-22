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


def test_run_calls_on_progress_for_each_pattern(monkeypatch, tmp_path):
    monkeypatch.setattr(
        adr_agent, "generate_adr", lambda pattern, number, model=None, api_key=None: f"CONTENT for {pattern['name']}"
    )

    calls = []
    adr_agent.run(
        patterns=["Saga", "Domain event"],
        output_dir=str(tmp_path),
        on_progress=lambda completed, total, result: calls.append((completed, total, result["pattern"])),
    )

    assert calls == [(1, 2, "Saga"), (2, 2, "Domain event")]
