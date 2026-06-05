import json
import re
from pathlib import Path
from openai import OpenAI

# Get prompt.md path relative to this file's location
PROMPT_TEMPLATE_PATH = Path(__file__).parent / "prompt.md"


class ArchScorer:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def _build_prompt(self, prd_text: str, predicted_puml: str) -> str:
        return (
            self.prompt_template
            .replace("{{INSERT_PRD_HERE}}", prd_text)
            .replace("{{INSERT_CODE_HERE}}", predicted_puml)
        )

    def score(self, prd_text: str, predicted_puml: str) -> dict:
        prompt = self._build_prompt(prd_text, predicted_puml)
        print(f"    -> Calling ArchScorer ({self.model_name}) for rubric scoring...")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            stream_options={"include_usage": True},
        )
        chunks = []
        usage = None
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    chunks.append(delta.content)
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
        raw = "".join(chunks)

        m = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
        json_str = m.group(1) if m else raw

        result = json.loads(json_str)

        if usage:
            prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
            completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
            result["_usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        return result

    @staticmethod
    def extract_scores(result: dict) -> dict:
        scores = result.get("scores", {})
        return {
            "Score_Completeness": scores.get("completeness", {}).get("score"),
            "Score_Accuracy":     scores.get("accuracy",     {}).get("score"),
            "Score_Rationality":  scores.get("rationality",  {}).get("score"),
            "Score_Readability":  scores.get("readability",  {}).get("score"),
        }
