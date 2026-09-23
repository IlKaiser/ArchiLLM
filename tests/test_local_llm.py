from src.local_llm import get_local_llm_config


def test_vllm_uses_openai_compatible_config():
    config = get_local_llm_config(
        "vllm", "Qwen/Qwen3.8-27B", "http://192.168.0.155:8000"
    )

    assert config == {
        "model": "openai/Qwen/Qwen3.8-27B",
        "api_key": "local",
        "base_url": "http://192.168.0.155:8000/v1",
        "max_output_tokens": 8192,
        "reasoning_effort": "none",
        "litellm_extra_body": {
            "chat_template_kwargs": {"enable_thinking": False},
        },
        "direct_generation": False,
        "relaxed_output": False,
    }


def test_vllm_does_not_duplicate_v1_suffix():
    config = get_local_llm_config("vllm", "openai/model", "http://localhost:8000/v1/")

    assert config["model"] == "openai/model"
    assert config["base_url"] == "http://localhost:8000/v1"
