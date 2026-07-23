import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability


def _write_project(tmp_path, project_name="demo"):
    run_dir = tmp_path / "run" / project_name
    run_dir.mkdir(parents=True)
    architecture = {"microservices": [{"name": "order_service"}], "patterns": [], "datastores": [], "dependencies": []}
    (run_dir / "architecture.json").write_text(json.dumps(architecture), encoding="utf-8")
    (run_dir / "component_diagram.puml").write_text(
        "@startuml\n[order_service]\n@enduml", encoding="utf-8"
    )

    dataset_dir = tmp_path / "dataset" / project_name
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "input.txt").write_text(
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n# USER STORIES:\n1. As a user, I want to place orders.",
        encoding="utf-8",
    )
    return architecture


def test_load_original_raises_when_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        modifiability._load_original(str(tmp_path / "run"), "does-not-exist")


def test_run_raises_file_not_found_when_project_not_yet_generated(tmp_path):
    with pytest.raises(FileNotFoundError):
        modifiability.run(
            "does-not-exist",
            run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
        )


def test_run_scores_scenarios_and_writes_report(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},
        {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    assert report["project"] == "demo"
    assert report["n_scenarios"] == 2
    assert len(report["scenarios"]) == 2
    for scenario in report["scenarios"]:
        assert scenario["ged"] is not None
        assert scenario["exact"] is True
        assert scenario["weighted_ged"] == scenario["weight"] * scenario["ged"]
    weighted_geds = [s["weighted_ged"] for s in report["scenarios"]]
    assert report["modifiability_score"] == round(sum(weighted_geds) / len(weighted_geds), 2)
    assert "small" in report["by_magnitude"]
    assert "large" in report["by_magnitude"]

    # The fixture's original diagram ("@startuml\n[order_service]\n@enduml")
    # has exactly 1 component and 0 dependency edges.
    assert report["original_node_count"] == 1
    assert report["original_edge_count"] == 0

    report_path = tmp_path / "run" / "demo" / "modifiability" / "report.json"
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_run_passes_original_diagram_text_to_render_step(tmp_path, monkeypatch):
    """render_scenario_diagram must be called with the project's actual
    existing diagram text, so it can adapt it in place rather than
    regenerating a fresh one from scratch for every scenario.
    """
    _write_project(tmp_path)

    fake_scenarios = [{"description": "Add SMS notifications", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )

    captured = {}

    def capturing_render(arch, **kwargs):
        captured.update(kwargs)
        return "@startuml\n[order_service]\n[new_service]\n@enduml"

    monkeypatch.setattr(modifiability, "render_scenario_diagram", capturing_render)

    modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    # _write_project's fixture writes exactly this as the original diagram.
    assert captured["original_diagram"] == "@startuml\n[order_service]\n@enduml"


def test_load_or_generate_scenarios_generates_and_saves_when_no_cache(tmp_path, monkeypatch):
    fake_scenarios = [{"description": "Add SMS notifications", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)

    report_dir = tmp_path / "modifiability"
    report_dir.mkdir()

    scenarios = modifiability._load_or_generate_scenarios(
        report_dir, "some input text", n_scenarios=1, regenerate_scenarios=False,
    )

    assert scenarios == fake_scenarios
    scenarios_path = report_dir / "scenarios.json"
    assert scenarios_path.exists()
    assert json.loads(scenarios_path.read_text(encoding="utf-8")) == fake_scenarios


def test_load_or_generate_scenarios_reuses_saved_scenarios(tmp_path, monkeypatch):
    report_dir = tmp_path / "modifiability"
    report_dir.mkdir()
    original_scenarios = [{"description": "Original scenario", "weight": 2, "magnitude": "medium"}]
    (report_dir / "scenarios.json").write_text(json.dumps(original_scenarios), encoding="utf-8")

    # If this were called, it would return a DIFFERENT scenario set — proving
    # that reuse (not regeneration) is what actually happened.
    def should_not_be_called(input_text, n, **kwargs):
        raise AssertionError("generate_scenarios must not be called when a cache exists")

    monkeypatch.setattr(modifiability, "generate_scenarios", should_not_be_called)

    scenarios = modifiability._load_or_generate_scenarios(
        report_dir, "some input text", n_scenarios=1, regenerate_scenarios=False,
    )

    assert scenarios == original_scenarios


def test_load_or_generate_scenarios_regenerates_when_requested(tmp_path, monkeypatch):
    report_dir = tmp_path / "modifiability"
    report_dir.mkdir()
    original_scenarios = [{"description": "Original scenario", "weight": 2, "magnitude": "medium"}]
    (report_dir / "scenarios.json").write_text(json.dumps(original_scenarios), encoding="utf-8")

    new_scenarios = [{"description": "New scenario", "weight": 4, "magnitude": "large"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: new_scenarios)

    scenarios = modifiability._load_or_generate_scenarios(
        report_dir, "some input text", n_scenarios=1, regenerate_scenarios=True,
    )

    assert scenarios == new_scenarios
    assert json.loads((report_dir / "scenarios.json").read_text(encoding="utf-8")) == new_scenarios


def test_run_reuses_saved_scenarios_across_separate_calls(tmp_path, monkeypatch):
    """Once run() has generated scenarios for a project, a second call must
    score the SAME scenarios by default (not roll a new random set), so
    results stay comparable across re-scoring runs.
    """
    _write_project(tmp_path)

    first_scenarios = [{"description": "First-run scenario", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: first_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    first_report = modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )
    assert first_report["scenarios"][0]["description"] == "First-run scenario"

    # A second call, even with a generate_scenarios mock that would return
    # something completely different, must reuse the saved scenario set.
    def should_not_be_called(input_text, n, **kwargs):
        raise AssertionError("generate_scenarios must not be called on a re-run with saved scenarios")

    monkeypatch.setattr(modifiability, "generate_scenarios", should_not_be_called)

    second_report = modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )
    assert second_report["scenarios"][0]["description"] == "First-run scenario"


def test_run_regenerates_scenarios_when_requested(tmp_path, monkeypatch):
    _write_project(tmp_path)

    first_scenarios = [{"description": "First-run scenario", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: first_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    second_scenarios = [{"description": "Regenerated scenario", "weight": 4, "magnitude": "large"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: second_scenarios)

    second_report = modifiability.run(
        "demo", n_scenarios=1, regenerate_scenarios=True,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )
    assert second_report["scenarios"][0]["description"] == "Regenerated scenario"


def test_archive_if_exists_moves_file_into_archive_dir(tmp_path):
    src = tmp_path / "report.json"
    src.write_text("{}", encoding="utf-8")
    archive_dir = tmp_path / "archive" / "20260101_000000_000000"

    modifiability._archive_if_exists(src, archive_dir)

    assert not src.exists()
    assert (archive_dir / "report.json").read_text(encoding="utf-8") == "{}"


def test_archive_if_exists_noop_when_source_missing(tmp_path):
    archive_dir = tmp_path / "archive" / "20260101_000000_000000"
    modifiability._archive_if_exists(tmp_path / "does_not_exist.json", archive_dir)
    assert not archive_dir.exists()


def test_archive_if_exists_noop_when_no_archive_dir_given(tmp_path):
    src = tmp_path / "report.json"
    src.write_text("{}", encoding="utf-8")
    modifiability._archive_if_exists(src, None)
    assert src.exists()  # left in place, since no archive_dir was given


def _run_demo(tmp_path, monkeypatch, description, weight="3", magnitude="small", **run_kwargs):
    scenarios = [{"description": description, "weight": int(weight), "magnitude": magnitude}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )
    return modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
        **run_kwargs,
    )


def test_run_archives_previous_report_and_scenario_dirs_before_overwriting(tmp_path, monkeypatch):
    _write_project(tmp_path)

    _run_demo(tmp_path, monkeypatch, "First run scenario")
    modifiability_dir = tmp_path / "run" / "demo" / "modifiability"
    first_run_input = (modifiability_dir / "scenario_01" / "input.txt").read_text(encoding="utf-8")
    assert "First run scenario" in first_run_input

    _run_demo(tmp_path, monkeypatch, "Second run scenario", regenerate_scenarios=True)

    # The live scenario_01/ must now reflect the SECOND run.
    second_run_input = (modifiability_dir / "scenario_01" / "input.txt").read_text(encoding="utf-8")
    assert "Second run scenario" in second_run_input
    assert "First run scenario" not in second_run_input

    # The FIRST run's report + scenario_01 must be preserved somewhere under archive/.
    archive_root = modifiability_dir / "archive"
    assert archive_root.exists()
    timestamped_dirs = list(archive_root.iterdir())
    assert len(timestamped_dirs) == 1
    archived_input = (timestamped_dirs[0] / "scenario_01" / "input.txt").read_text(encoding="utf-8")
    assert "First run scenario" in archived_input
    assert (timestamped_dirs[0] / "report.json").exists()


def test_run_does_not_archive_scenarios_json_when_only_rescoring(tmp_path, monkeypatch):
    """Reusing the same saved scenarios (not regenerating them) must leave
    scenarios.json in place, untouched — nothing is changing for it.
    """
    _write_project(tmp_path)

    _run_demo(tmp_path, monkeypatch, "A scenario")
    modifiability_dir = tmp_path / "run" / "demo" / "modifiability"
    original_scenarios_json = (modifiability_dir / "scenarios.json").read_text(encoding="utf-8")

    # Second call: regenerate_scenarios defaults to False, so this re-scores
    # the SAME cached scenario, not a new one — the mock returning a
    # different description is irrelevant since generate_scenarios won't be
    # called again.
    _run_demo(tmp_path, monkeypatch, "Would-be different scenario")

    assert (modifiability_dir / "scenarios.json").read_text(encoding="utf-8") == original_scenarios_json
    assert not (modifiability_dir / "archive").exists() or not any(
        (d / "scenarios.json").exists() for d in (modifiability_dir / "archive").iterdir()
    )


def test_run_archives_old_scenarios_json_when_regenerating(tmp_path, monkeypatch):
    _write_project(tmp_path)

    _run_demo(tmp_path, monkeypatch, "First scenario")
    modifiability_dir = tmp_path / "run" / "demo" / "modifiability"
    first_scenarios_json = (modifiability_dir / "scenarios.json").read_text(encoding="utf-8")

    _run_demo(tmp_path, monkeypatch, "Second scenario", regenerate_scenarios=True)

    new_scenarios_json = (modifiability_dir / "scenarios.json").read_text(encoding="utf-8")
    assert new_scenarios_json != first_scenarios_json
    assert "Second scenario" in new_scenarios_json

    archive_root = modifiability_dir / "archive"
    archived_scenarios = [d / "scenarios.json" for d in archive_root.iterdir() if (d / "scenarios.json").exists()]
    assert len(archived_scenarios) == 1
    assert archived_scenarios[0].read_text(encoding="utf-8") == first_scenarios_json


def test_build_updated_spec_appends_new_story_with_next_number():
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n1. As a user, I want to place orders.\n2. As a user, I want to cancel orders."
    )

    updated = modifiability._build_updated_spec(
        original, ["As a user, I want to receive SMS notifications, so that I stay informed."]
    )

    assert original in updated
    assert updated.endswith(
        "3. As a user, I want to receive SMS notifications, so that I stay informed.\n"
    )


def test_build_updated_spec_starts_at_one_when_no_numbered_stories():
    updated = modifiability._build_updated_spec(
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n# USER STORIES:\n", ["A brand new story."]
    )
    assert updated.endswith("1. A brand new story.\n")


def test_build_updated_spec_supports_multiple_new_stories_for_medium_large_magnitude():
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n1. As a user, I want to place orders.\n2. As a user, I want to cancel orders."
    )

    updated = modifiability._build_updated_spec(
        original,
        ["As a user, I want story A.", "As a user, I want story B.", "As a user, I want story C."],
    )

    assert updated.endswith(
        "3. As a user, I want story A.\n4. As a user, I want story B.\n5. As a user, I want story C.\n"
    )


def test_build_updated_spec_removes_and_renumbers_when_story_retired():
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n"
        "1. As a user, I want to place orders.\n"
        "2. As a user, I want the OLD slow checkout flow.\n"
        "3. As a user, I want to cancel orders.\n"
    )

    updated = modifiability._build_updated_spec(
        original,
        ["As a user, I want the NEW fast checkout flow."],
        removed_user_story_numbers=[2],
    )

    # The retired story must be gone, everything else renumbered
    # sequentially, and the new story appended at the end.
    assert "OLD slow checkout flow" not in updated
    assert updated == (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n"
        "1. As a user, I want to place orders.\n"
        "2. As a user, I want to cancel orders.\n"
        "3. As a user, I want the NEW fast checkout flow.\n"
    )


def test_resolve_removed_stories_looks_up_text_by_number():
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n"
        "1. As a user, I want to place orders.\n"
        "2. As a user, I want the OLD slow checkout flow.\n"
    )
    assert modifiability._resolve_removed_stories(original, [2]) == [
        "As a user, I want the OLD slow checkout flow."
    ]


def test_resolve_removed_stories_skips_unknown_numbers():
    original = "# USER STORIES:\n1. As a user, I want to place orders.\n"
    assert modifiability._resolve_removed_stories(original, [99]) == []


def test_resolve_removed_stories_empty_when_no_numbers_given():
    assert modifiability._resolve_removed_stories("anything", []) == []


def test_run_handles_multiple_new_stories_and_a_removal_end_to_end(tmp_path, monkeypatch):
    """A 'large' magnitude scenario with several new stories and a removed
    one must flow all the way through: input.txt reflects the net change,
    and modify_architecture receives a combined description covering both
    the additions and the retirement.
    """
    _write_project(tmp_path)
    (tmp_path / "dataset" / "demo" / "input.txt").write_text(
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n# USER STORIES:\n"
        "1. As a user, I want to place orders.\n"
        "2. As a user, I want the OLD slow checkout flow.\n",
        encoding="utf-8",
    )

    fake_scenarios = [
        {
            "description": "Overhaul checkout with fast-path + loyalty program",
            "weight": 5,
            "magnitude": "large",
            "new_user_stories": [
                "As a user, I want a one-click fast checkout, so that I save time.",
                "As a user, I want to earn loyalty points on checkout, so that I'm rewarded.",
            ],
            "removed_user_story_numbers": [2],
        },
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)

    captured = {}

    def capturing_modify(arch, scenario_text, **kwargs):
        captured["scenario_text"] = scenario_text
        return {"microservices": [{"name": "order_service"}, {"name": "loyalty_service"}]}

    monkeypatch.setattr(modifiability, "modify_architecture", capturing_modify)
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[loyalty_service]\n@enduml",
    )

    modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    # modify_architecture must see both the new stories and the retirement.
    assert "one-click fast checkout" in captured["scenario_text"]
    assert "earn loyalty points" in captured["scenario_text"]
    assert "OLD slow checkout flow" in captured["scenario_text"]

    spec_path = tmp_path / "run" / "demo" / "modifiability" / "scenario_01" / "input.txt"
    content = spec_path.read_text(encoding="utf-8")
    assert "OLD slow checkout flow" not in content
    assert "1. As a user, I want to place orders." in content
    assert "one-click fast checkout" in content
    assert "earn loyalty points" in content


def test_run_writes_updated_spec_per_scenario(tmp_path, monkeypatch):
    """Each scenario's full updated spec (original user stories + the new
    one) must be saved to disk alongside the modified architecture/diagram,
    so the exact input that drove that variation is inspectable.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {
            "description": "As a user, I want to receive SMS notifications, so that I stay informed.",
            "weight": 3, "magnitude": "small",
        },
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    spec_path = tmp_path / "run" / "demo" / "modifiability" / "scenario_01" / "input.txt"
    assert spec_path.exists()
    content = spec_path.read_text(encoding="utf-8")
    # The fixture's original story ("1. As a user, I want to place orders.")
    # must still be present, plus the new one appended as "2.".
    assert "1. As a user, I want to place orders." in content
    assert content.endswith(
        "2. As a user, I want to receive SMS notifications, so that I stay informed.\n"
    )


def test_compute_spec_delta_shows_only_the_added_line():
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n1. As a user, I want to place orders.\n"
    )
    updated = modifiability._build_updated_spec(
        original, ["As a user, I want to receive SMS notifications, so that I stay informed."]
    )

    delta = modifiability._compute_spec_delta(original, updated)

    assert "+2. As a user, I want to receive SMS notifications, so that I stay informed." in delta
    # The unchanged original line must not show up as a removal.
    assert "-1. As a user, I want to place orders." not in delta


def test_compute_spec_delta_empty_when_texts_are_identical():
    text = "# SYSTEM DESCRIPTION:\nAn order system.\n"
    assert modifiability._compute_spec_delta(text, text) == ""


def test_compute_spec_delta_ignores_missing_trailing_newline_on_original():
    """A source input.txt with no trailing newline (common) must not make
    the last unchanged line show up as both removed and re-added just
    because _build_updated_spec appends a newline before the new story.
    """
    original = (
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n"
        "# USER STORIES:\n1. As a user, I want to place orders."  # no trailing \n
    )
    updated = modifiability._build_updated_spec(original, ["A brand new story."])

    delta = modifiability._compute_spec_delta(original, updated)

    assert "-1. As a user, I want to place orders." not in delta
    assert "+2. A brand new story." in delta


def test_run_writes_spec_delta_per_scenario(tmp_path, monkeypatch):
    """Each scenario's textual delta (vs. the original spec) must be saved
    to disk as its own artifact, not just be derivable by manually diffing
    input.txt files.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {
            "description": "As a user, I want to receive SMS notifications, so that I stay informed.",
            "weight": 3, "magnitude": "small",
        },
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    delta_path = tmp_path / "run" / "demo" / "modifiability" / "scenario_01" / "spec_delta.txt"
    assert delta_path.exists()
    content = delta_path.read_text(encoding="utf-8")
    assert "+2. As a user, I want to receive SMS notifications, so that I stay informed." in content


def test_backfill_spec_deltas_writes_missing_deltas_for_existing_scenarios(tmp_path):
    """Scenario directories generated before spec_delta.txt existed (they
    only have input.txt) must get a delta computed and written on demand,
    without needing to re-run the whole (LLM-driven) analysis.
    """
    _write_project(tmp_path)

    modifiability_dir = tmp_path / "run" / "demo" / "modifiability"
    scenario_dir = modifiability_dir / "scenario_01"
    scenario_dir.mkdir(parents=True)
    (scenario_dir / "input.txt").write_text(
        "# SYSTEM DESCRIPTION:\nAn order system.\n\n# USER STORIES:\n"
        "1. As a user, I want to place orders.\n"
        "2. As a user, I want to receive SMS notifications, so that I stay informed.\n",
        encoding="utf-8",
    )
    # A scenario directory with no input.txt at all (e.g. it failed before
    # any artifact was written) must be silently skipped, not raise.
    (modifiability_dir / "scenario_02").mkdir(parents=True)

    written = modifiability.backfill_spec_deltas(
        "demo", run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    assert written == 1
    delta_path = scenario_dir / "spec_delta.txt"
    assert delta_path.exists()
    assert "+2. As a user, I want to receive SMS notifications, so that I stay informed." in (
        delta_path.read_text(encoding="utf-8")
    )
    assert not (modifiability_dir / "scenario_02" / "spec_delta.txt").exists()


def test_backfill_spec_deltas_returns_zero_when_no_scenarios_exist(tmp_path):
    _write_project(tmp_path)
    (tmp_path / "run" / "demo" / "modifiability").mkdir(parents=True)

    written = modifiability.backfill_spec_deltas(
        "demo", run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )
    assert written == 0


def test_run_writes_intermediate_artifacts_per_scenario(tmp_path, monkeypatch):
    """Each scenario's modified architecture.json and rendered
    component_diagram.puml must be saved to disk, not just held in memory
    for the final aggregated report.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},
        {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    modifiability_dir = tmp_path / "run" / "demo" / "modifiability"
    for i, scenario in enumerate(report["scenarios"], start=1):
        scenario_dir = modifiability_dir / f"scenario_{i:02d}"
        assert scenario["artifacts_dir"] == str(scenario_dir)

        arch_path = scenario_dir / "architecture.json"
        puml_path = scenario_dir / "component_diagram.puml"
        assert arch_path.exists()
        assert puml_path.exists()
        assert json.loads(arch_path.read_text(encoding="utf-8")) == {
            "microservices": [{"name": "order_service"}, {"name": "new_service"}]
        }
        assert puml_path.read_text(encoding="utf-8") == "@startuml\n[order_service]\n[new_service]\n@enduml"


def test_run_saves_partial_artifacts_when_render_fails_after_edit_succeeds(tmp_path, monkeypatch):
    """If modify_architecture succeeds but render_scenario_diagram then
    fails, the already-produced architecture.json must still be saved for
    inspection, not discarded just because the scenario ultimately errored.
    """
    _write_project(tmp_path)

    fake_scenarios = [{"description": "Will partially fail", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )

    def failing_render(arch, **kwargs):
        raise ValueError("render exploded")

    monkeypatch.setattr(modifiability, "render_scenario_diagram", failing_render)

    report = modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    scenario = report["scenarios"][0]
    assert scenario["ged"] is None
    assert "error" in scenario

    scenario_dir = tmp_path / "run" / "demo" / "modifiability" / "scenario_01"
    assert (scenario_dir / "architecture.json").exists()
    assert not (scenario_dir / "component_diagram.puml").exists()


def test_modifiability_score_is_average_not_sum_of_weighted_ged(tmp_path, monkeypatch):
    """The headline score must be the mean of the successfully-scored
    scenarios' weighted_ged, not their sum — otherwise running more
    scenarios would inflate the score even if each one is individually small.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Scenario A", "weight": 1, "magnitude": "small"},
        {"description": "Scenario B", "weight": 1, "magnitude": "small"},
        {"description": "Scenario C", "weight": 1, "magnitude": "small"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)

    fake_results = iter([
        {"weighted_ged": 10.0}, {"weighted_ged": 20.0}, {"weighted_ged": 30.0},
    ])

    def fake_score_one_scenario(scenario, architecture, g_original, timeout, *args, **kwargs):
        return {**scenario, "ged": 1.0, "exact": True, **next(fake_results)}

    monkeypatch.setattr(modifiability, "_score_one_scenario", fake_score_one_scenario)

    report = modifiability.run(
        "demo", n_scenarios=3,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    # Mean of [10, 20, 30] is 20 — the sum (60) would be a different, wrong answer.
    assert report["modifiability_score"] == 20.0


def test_modifiability_score_is_zero_when_no_scenario_scores_successfully(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [{"description": "Will fail", "weight": 3, "magnitude": "small"}]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)

    def always_fails(scenario, architecture, g_original, timeout, *args, **kwargs):
        return {**scenario, "error": "boom", "ged": None, "exact": False, "weighted_ged": None}

    monkeypatch.setattr(modifiability, "_score_one_scenario", always_fails)

    report = modifiability.run(
        "demo", n_scenarios=1,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    assert report["modifiability_score"] == 0.0


def test_run_calls_on_progress_for_each_scenario(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},
        {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[new_service]\n@enduml",
    )

    calls = []
    modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
        on_progress=lambda completed, total, result: calls.append((completed, total, result["description"])),
    )

    assert calls == [
        (1, 2, "Add SMS notifications"),
        (2, 2, "Support multi-region deployment"),
    ]


def test_run_continues_after_one_scenario_failure(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Will fail", "weight": 2, "magnitude": "small"},
        {"description": "Will succeed", "weight": 4, "magnitude": "medium"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)

    def flaky_modify(architecture, description, **kwargs):
        if "Will fail" in description:
            raise ValueError("LLM exploded")
        return {"microservices": [{"name": "order_service"}, {"name": "extra"}]}

    monkeypatch.setattr(modifiability, "modify_architecture", flaky_modify)
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[extra]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    failed, succeeded = report["scenarios"]
    assert failed["ged"] is None
    assert failed["exact"] is False
    assert "error" in failed
    assert succeeded["ged"] is not None
    assert succeeded["weighted_ged"] == succeeded["weight"] * succeeded["ged"]
    # aggregate must only include the successful scenario
    assert report["modifiability_score"] == round(succeeded["weighted_ged"], 2)


def test_run_continues_when_scenario_has_malformed_weight(tmp_path, monkeypatch):
    """A scenario missing 'weight' (or with a non-numeric weight) — e.g. from
    unvalidated LLM-generated JSON — must not abort the whole batch. It
    should be scored as a graceful per-scenario failure while the other
    scenario(s) still get scored and the report still gets written.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Missing weight", "magnitude": "small"},  # no "weight" key
        {"description": "Bad weight type", "weight": "not-a-number", "magnitude": "medium"},
        {"description": "Will succeed", "weight": 4, "magnitude": "large"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}, {"name": "extra"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch, **kwargs: "@startuml\n[order_service]\n[extra]\n@enduml",
    )

    report = modifiability.run(
        "demo", n_scenarios=3,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    missing_weight, bad_weight, succeeded = report["scenarios"]

    assert missing_weight["ged"] is None
    assert missing_weight["exact"] is False
    assert missing_weight["weighted_ged"] is None
    assert "error" in missing_weight

    assert bad_weight["ged"] is None
    assert bad_weight["exact"] is False
    assert bad_weight["weighted_ged"] is None
    assert "error" in bad_weight

    assert succeeded["ged"] is not None
    assert succeeded["weighted_ged"] == succeeded["weight"] * succeeded["ged"]

    # The report must still be written, and the score/aggregation must only
    # reflect the one scenario that actually scored.
    assert report["modifiability_score"] == round(succeeded["weighted_ged"], 2)
    report_path = tmp_path / "run" / "demo" / "modifiability" / "report.json"
    assert report_path.exists()


def test_run_treats_unparseable_render_as_inconclusive(tmp_path, monkeypatch):
    """If modify_architecture + render_scenario_diagram produce PlantUML text
    with no parseable components (e.g. missing @startuml), the scenario must
    be treated as inconclusive (ged: None, exact: False) rather than being
    scored as a huge, exact graph-edit distance against an empty graph.
    """
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Renders to garbage", "weight": 3, "magnitude": "large"},
        {"description": "Will succeed", "weight": 2, "magnitude": "small"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n, **kwargs: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc, **kwargs: {"microservices": [{"name": "order_service"}]},
    )

    # Distinguish the two scenarios by call order via a stateful closure,
    # since both scenarios call modify_architecture with the same arch stub
    # and scenarios are scored in order.
    calls = {"n": 0}

    def render_by_call_order(arch, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not a plantuml diagram at all"
        return "@startuml\n[order_service]\n[extra]\n@enduml"

    monkeypatch.setattr(modifiability, "render_scenario_diagram", render_by_call_order)

    report = modifiability.run(
        "demo", n_scenarios=2,
        run_dir=str(tmp_path / "run"), dataset_dir=str(tmp_path / "dataset"),
    )

    garbage, succeeded = report["scenarios"]

    assert garbage["ged"] is None
    assert garbage["exact"] is False
    assert garbage["weighted_ged"] is None
    assert "error" in garbage

    assert succeeded["ged"] is not None
    assert succeeded["exact"] is True
    assert succeeded["weighted_ged"] == succeeded["weight"] * succeeded["ged"]

    # The inconclusive scenario must be excluded from both the headline
    # score and the by-magnitude aggregation, not counted as a huge distance.
    assert report["modifiability_score"] == round(succeeded["weighted_ged"], 2)
    assert "large" not in report["by_magnitude"]
    assert "small" in report["by_magnitude"]
