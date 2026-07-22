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
