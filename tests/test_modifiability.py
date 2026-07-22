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
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n: fake_scenarios)
    monkeypatch.setattr(
        modifiability, "modify_architecture",
        lambda arch, desc: {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
    )
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch: "@startuml\n[order_service]\n[new_service]\n@enduml",
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

    report_path = tmp_path / "run" / "demo" / "modifiability" / "report.json"
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_run_continues_after_one_scenario_failure(tmp_path, monkeypatch):
    _write_project(tmp_path)

    fake_scenarios = [
        {"description": "Will fail", "weight": 2, "magnitude": "small"},
        {"description": "Will succeed", "weight": 4, "magnitude": "medium"},
    ]
    monkeypatch.setattr(modifiability, "generate_scenarios", lambda input_text, n: fake_scenarios)

    def flaky_modify(architecture, description):
        if description == "Will fail":
            raise ValueError("LLM exploded")
        return {"microservices": [{"name": "order_service"}, {"name": "extra"}]}

    monkeypatch.setattr(modifiability, "modify_architecture", flaky_modify)
    monkeypatch.setattr(
        modifiability, "render_scenario_diagram",
        lambda arch: "@startuml\n[order_service]\n[extra]\n@enduml",
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
