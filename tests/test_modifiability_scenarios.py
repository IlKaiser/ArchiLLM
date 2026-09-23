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


def test_render_scenario_diagram_uses_plain_prompt_without_original(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "@startuml\n[order_service]\n@enduml"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    ms.render_scenario_diagram({"microservices": []}, model="test/model", api_key="test-key")

    prompt_text = fake_completion.call_args.kwargs["messages"][0]["content"]
    assert "## Original Diagram" not in prompt_text
    assert "Generate a valid PlantUML component diagram" in prompt_text


def test_render_scenario_diagram_adapts_original_when_given(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "@startuml\n[order_service]\n[new_service]\n@enduml"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)

    original = "@startuml\n[order_service]\n@enduml"
    result = ms.render_scenario_diagram(
        {"microservices": [{"name": "order_service"}, {"name": "new_service"}]},
        original_diagram=original,
        model="test/model", api_key="test-key",
    )

    assert result == "@startuml\n[order_service]\n[new_service]\n@enduml"
    prompt_text = fake_completion.call_args.kwargs["messages"][0]["content"]
    assert "## Original Diagram" in prompt_text
    assert original in prompt_text
    assert "new_service" in prompt_text


def test_complete_appends_cost_to_tracker_when_given(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    monkeypatch.setattr(ms.litellm, "completion", MagicMock(return_value=fake_response))
    monkeypatch.setattr(ms.litellm, "completion_cost", MagicMock(return_value=0.0042))

    cost_tracker: list[float] = []
    ms._complete("a prompt", model="test/model", api_key="test-key", cost_tracker=cost_tracker)

    assert cost_tracker == [0.0042]


def test_complete_swallows_cost_calculation_failure(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    monkeypatch.setattr(ms.litellm, "completion", MagicMock(return_value=fake_response))
    monkeypatch.setattr(ms.litellm, "completion_cost", MagicMock(side_effect=Exception("unknown model")))

    cost_tracker: list[float] = []
    result = ms._complete("a prompt", model="test/model", api_key="test-key", cost_tracker=cost_tracker)

    assert result == "some text"
    assert cost_tracker == []


def test_complete_passes_a_timeout_to_litellm_by_default(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)
    monkeypatch.delenv("LLM_REQUEST_TIMEOUT", raising=False)

    ms._complete("a prompt", model="test/model", api_key="test-key")

    assert fake_completion.call_args.kwargs["timeout"] == 180.0


def test_complete_respects_llm_request_timeout_env_var(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "45")

    ms._complete("a prompt", model="test/model", api_key="test-key")

    assert fake_completion.call_args.kwargs["timeout"] == 45.0


def test_complete_explicit_timeout_overrides_env_and_default(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT", "45")

    ms._complete("a prompt", model="test/model", api_key="test-key", timeout=12.5)

    assert fake_completion.call_args.kwargs["timeout"] == 12.5


def test_complete_passes_openai_compatible_base_url(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)
    monkeypatch.setenv("LLM_BASE_URL", "http://192.168.0.155:8000/v1/")

    ms._complete("a prompt", model="openai/Qwen/Qwen3.8-27B", api_key="local")

    assert fake_completion.call_args.kwargs["api_base"] == "http://192.168.0.155:8000/v1"


def test_complete_can_disable_thinking_and_bound_output(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = "some text"
    fake_completion = MagicMock(return_value=fake_response)
    monkeypatch.setattr(ms.litellm, "completion", fake_completion)
    monkeypatch.setenv("LLM_DISABLE_THINKING", "1")
    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "8192")

    ms._complete("a prompt", model="openai/Qwen/Qwen3.8-27B", api_key="local")

    kwargs = fake_completion.call_args.kwargs
    assert kwargs["max_tokens"] == 8192
    assert kwargs["extra_body"] == {
        "chat_template_kwargs": {"enable_thinking": False},
    }


def test_generate_scenarios_forwards_cost_tracker(monkeypatch):
    fake_response = MagicMock()
    fake_response.choices[0].message.content = '```json\n[{"description": "X", "weight": 1, "magnitude": "small"}]\n```'
    monkeypatch.setattr(ms.litellm, "completion", MagicMock(return_value=fake_response))
    monkeypatch.setattr(ms.litellm, "completion_cost", MagicMock(return_value=0.001))

    cost_tracker: list[float] = []
    ms.generate_scenarios("input", n=1, cost_tracker=cost_tracker)

    assert cost_tracker == [0.001]
