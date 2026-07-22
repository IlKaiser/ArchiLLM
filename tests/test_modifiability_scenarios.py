import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Evaluation import modifiability_scenarios as ms


def test_extract_json_parses_fenced_array():
    raw = '```json\n[{"a": 1}]\n```'
    assert ms._extract_json(raw) == [{"a": 1}]


def test_extract_json_parses_bare_object_without_fence():
    raw = '{"a": 1}'
    assert ms._extract_json(raw) == {"a": 1}


def test_generate_scenarios_calls_litellm_and_parses_json(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = (
        '```json\n'
        '[{"description": "Add SMS notifications", "weight": 3, "magnitude": "small"},'
        ' {"description": "Support multi-region deployment", "weight": 5, "magnitude": "large"}]'
        '\n```'
    )
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    scenarios = ms.generate_scenarios("some input text", n=2, model="test/model", api_key="test-key")

    assert len(scenarios) == 2
    assert scenarios[0]["description"] == "Add SMS notifications"
    assert scenarios[1]["magnitude"] == "large"
    call_kwargs = fake_completion.call_args.kwargs
    assert call_kwargs["model"] == "test/model"
    assert call_kwargs["api_key"] == "test-key"
    assert "some input text" in call_kwargs["messages"][0]["content"]
    assert "2" in call_kwargs["messages"][0]["content"]


def test_modify_architecture_embeds_existing_architecture_and_scenario(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = '```json\n{"microservices": [], "patterns": []}\n```'
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    architecture = {"microservices": [{"name": "order_service"}], "patterns": []}
    result = ms.modify_architecture(architecture, "Add SMS notifications", model="test/model", api_key="test-key")

    assert result == {"microservices": [], "patterns": []}
    call_kwargs = fake_completion.call_args.kwargs
    prompt_text = call_kwargs["messages"][0]["content"]
    assert "order_service" in prompt_text
    assert "Add SMS notifications" in prompt_text


def test_render_scenario_diagram_returns_plain_puml_text(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "@startuml\n[order_service]\n@enduml"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    result = ms.render_scenario_diagram({"microservices": []}, model="test/model", api_key="test-key")

    assert result == "@startuml\n[order_service]\n@enduml"
