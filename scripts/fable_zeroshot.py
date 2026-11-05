#!/usr/bin/env python3
"""Zero-shot plain prompt with Claude Fable 5.1 (Anthropic Messages API).

Same prompt, PlantUML extraction and rendering as scripts/plain_prompt_baseline.py;
only the model call differs, because that script speaks the OpenAI chat format.
Fable always thinks (no `thinking` field is sent); depth is set with
`output_config.effort`, `high` to match the other models' high-reasoning runs.
Server-side refusal fallbacks are on (`fallbacks: "default"`); a fallback means
another model wrote the diagram, so the serving model is recorded in usage.json.

Writes per project, under --output/<project>/:
  component_diagram.puml / .png, raw_response.md, usage.json

    uv run --with 'anthropic>=2.4' python scripts/fable_zeroshot.py --project PENTION
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plain_prompt_baseline import PROMPT, REPO, extract_puml, load_dotenv, render_png  # noqa: E402

logger = logging.getLogger(__name__)

MODEL = "claude-fable-5-1"
PRICE_PER_MTOK = {"input": 10.0, "output": 50.0}  # USD, Claude Fable 5.1 first-party
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def run_project(client: anthropic.Anthropic, name: str, args: argparse.Namespace) -> dict:
    """One zero-shot call for `name`; writes its outputs and returns the usage record."""
    out_dir = REPO / args.output / name
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = (REPO / args.dataset / name / "input.txt").read_text(encoding="utf-8")
    start = time.monotonic()
    # Streaming: a high-effort Fable turn can run for minutes, past non-streaming HTTP timeouts.
    with client.beta.messages.stream(
        model=MODEL, max_tokens=args.max_tokens,
        output_config={"effort": args.effort},
        betas=[FALLBACK_BETA], fallbacks="default",
        messages=[{"role": "user", "content": PROMPT.format(spec=spec)}],
    ) as stream:
        message = stream.get_final_message()
    elapsed = round(time.monotonic() - start, 1)

    text = "".join(b.text for b in message.content if b.type == "text")
    (out_dir / "raw_response.md").write_text(text, encoding="utf-8")
    usage = message.usage
    fallback_ran = any(getattr(i, "type", "") == "fallback_message" for i in (usage.iterations or []))
    record = {
        "project": name, "requested_model": MODEL, "served_model": message.model,
        "fallback_ran": fallback_ran, "stop_reason": message.stop_reason, "effort": args.effort,
        "time_seconds": elapsed, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
        "cost_usd": round((usage.input_tokens * PRICE_PER_MTOK["input"]
                           + usage.output_tokens * PRICE_PER_MTOK["output"]) / 1e6, 4),
        "message_id": message.id,
    }
    if message.stop_reason == "refusal":
        record["error"] = f"refused: {message.stop_details}"
    elif (puml := extract_puml(text)) is None:
        record["error"] = f"no @startuml..@enduml block (stop_reason={message.stop_reason})"
    else:
        puml_path = out_dir / "component_diagram.puml"
        puml_path.write_text(puml, encoding="utf-8")
        record["rendered"] = render_png(puml_path)
    (out_dir / "usage.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", default="dataset/student_projects")
    parser.add_argument("--output", default="results/fable_plain_baseline/student_projects")
    parser.add_argument("--project", required=True, help="Comma-separated project name(s)")
    parser.add_argument("--effort", default="high", choices=("low", "medium", "high", "xhigh", "max"))
    parser.add_argument("--max-tokens", type=int, default=64000)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(REPO / ".env")  # ANTHROPIC_API_KEY; never overrides the real environment
    client = anthropic.Anthropic()
    for name in (p.strip() for p in args.project.split(",")):
        try:
            record = run_project(client, name, args)
        except anthropic.APIStatusError as e:
            logger.error("%s: API error %s (request %s): %s", name, e.status_code, e.request_id, e.message)
            continue
        except anthropic.APIConnectionError as e:
            logger.error("%s: connection error: %s", name, e)
            continue
        logger.info("%s: %s", name, json.dumps(record))


if __name__ == "__main__":
    main()
