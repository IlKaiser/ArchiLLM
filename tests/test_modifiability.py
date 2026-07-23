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
    assert report["modifiability_score"] == round(sum(s["weighted_ged"] for s in report["scenarios"]), 2)
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
        if description == "Will fail":
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
