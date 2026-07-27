import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest

from src import modifiability_frontend

HARNESS_PATH = str(Path(__file__).parent / "fixtures" / "modifiability_frontend_harness.py")
HARNESS_EMPTY_PATH = str(Path(__file__).parent / "fixtures" / "modifiability_frontend_harness_empty.py")
DOUBLE_RENDER_HARNESS_PATH = str(
    Path(__file__).parent / "fixtures" / "modifiability_double_render_harness.py"
)


def test_render_shows_run_button_when_project_selected():
    at = AppTest.from_file(HARNESS_PATH)
    at.run()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert "🔀 Run Modifiability Analysis" in button_labels


def test_render_report_twice_in_one_run_does_not_collide_on_widget_keys():
    """Regression test: render() calls _render_report once to preload an
    existing report and again after a fresh run, both in the same Streamlit
    script pass. Every widget with an explicit key (e.g. the "Visualize an
    Edit Distance Example" selectbox) must stay unique across that pair of
    calls, or Streamlit raises a duplicate-key error.
    """
    at = AppTest.from_file(DOUBLE_RENDER_HARNESS_PATH)
    at.run()
    assert not at.exception
    assert len(at.selectbox) == 2


def test_render_shows_info_when_no_project_selected():
    at = AppTest.from_file(HARNESS_EMPTY_PATH)
    at.run()
    assert not at.exception
    button_labels = [b.label for b in at.button]
    assert "🔀 Run Modifiability Analysis" not in button_labels


def test_scenario_table_rows_formats_missing_values():
    rows = modifiability_frontend._scenario_table_rows([
        {"description": "Add X", "weight": 3, "magnitude": "small", "ged": 2.0, "exact": True, "weighted_ged": 6.0},
        {"description": "Add Y", "weight": 4, "magnitude": "large", "ged": None, "exact": False, "weighted_ged": None},
    ])
    assert rows[0]["GED"] == 2.0
    assert rows[1]["GED"] == "—"
    assert rows[1]["Weighted GED"] == "—"


def test_scenario_chart_returns_none_when_no_scored_scenarios():
    chart = modifiability_frontend._scenario_chart([
        {"description": "Add X", "weight": 3, "magnitude": "small", "ged": None, "exact": False, "weighted_ged": None},
    ])
    assert chart is None


def test_scenario_chart_builds_altair_chart_with_magnitude_color_encoding():
    import altair as alt

    scenarios = [
        {"description": "Add X", "weight": 3, "magnitude": "small", "ged": 2.0, "exact": True, "weighted_ged": 6.0},
        {"description": "Add Y", "weight": 4, "magnitude": "large", "ged": 5.0, "exact": True, "weighted_ged": 20.0},
    ]
    chart = modifiability_frontend._scenario_chart(scenarios)

    assert isinstance(chart, alt.Chart)
    # Two rows fed in, one per non-null scenario.
    assert len(chart.data) == 2

    # Inspect the actual serialized Vega-Lite spec rather than Altair's
    # Python-object attributes: in altair==6.2.2 (the version installed
    # here, matching environment.yml's altair==6.0.0), `chart.encoding.color`
    # is a `_PropertySetter`, not a plain object with `.field`/`.scale`
    # attributes — `.to_dict()` is the stable, version-independent contract.
    color_spec = chart.to_dict()["encoding"]["color"]
    # Color is encoded by Magnitude on a fixed small->medium->large domain
    # (magnitude is ordinal, not an arbitrary category), never a free-cycled hue.
    assert color_spec["field"] == "Magnitude"
    assert color_spec["scale"]["domain"] == ["small", "medium", "large"]
    assert color_spec["scale"]["scheme"] == "blues"


def test_visualizable_scenarios_excludes_non_exact_and_sorts_by_weighted_ged_desc():
    scenarios = [
        {"description": "Small change", "weight": 2, "ged": 1.0, "exact": True,
         "weighted_ged": 2.0, "artifacts_dir": "/tmp/scenario_01"},
        {"description": "Failed", "weight": 3, "ged": None, "exact": False,
         "weighted_ged": None, "artifacts_dir": "/tmp/scenario_02"},
        {"description": "Big change", "weight": 5, "ged": 4.0, "exact": True,
         "weighted_ged": 20.0, "artifacts_dir": "/tmp/scenario_03"},
        {"description": "No artifacts dir", "weight": 1, "ged": 1.0, "exact": True, "weighted_ged": 1.0},
    ]

    result = modifiability_frontend._visualizable_scenarios(scenarios)

    assert [s["description"] for s in result] == ["Big change", "Small change"]


def test_load_existing_report_reads_json(tmp_path):
    report_dir = tmp_path / "demo" / "modifiability"
    report_dir.mkdir(parents=True)
    (report_dir / "report.json").write_text('{"modifiability_score": 5.0}', encoding="utf-8")

    report = modifiability_frontend._load_existing_report("demo", run_dir=str(tmp_path))
    assert report == {"modifiability_score": 5.0}


def test_load_existing_report_returns_none_when_missing(tmp_path):
    report = modifiability_frontend._load_existing_report("demo", run_dir=str(tmp_path))
    assert report is None


def test_scenarios_cached_true_when_scenarios_json_exists(tmp_path):
    scenarios_dir = tmp_path / "demo" / "modifiability"
    scenarios_dir.mkdir(parents=True)
    (scenarios_dir / "scenarios.json").write_text("[]", encoding="utf-8")

    assert modifiability_frontend._scenarios_cached("demo", run_dir=str(tmp_path)) is True


def test_scenarios_cached_false_when_missing(tmp_path):
    assert modifiability_frontend._scenarios_cached("demo", run_dir=str(tmp_path)) is False
