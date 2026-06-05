#!/usr/bin/env python3
"""
Standalone single-project evaluator.

Usage:
    python eval_single.py --project 4-by-4

Env vars (loaded from root .env):
    JUDGE_API_KEY   override API key (falls back to LLM_API_KEY)
    JUDGE_BASE_URL  OpenAI-compatible base URL (falls back to LLM_BASE_URL)
    JUDGE_MODEL     model name (falls back to LLM_MODEL)

Pass --no-llm to skip LLM calls and compute structural metrics only.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Resolve directories
EVAL_DIR = Path(__file__).parent.resolve()
ROOT = EVAL_DIR.parent

# Load project .env before importing anything that reads env
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass  # proceed with os.environ as-is

sys.path.insert(0, str(EVAL_DIR))

from uml_parser import UMLParser
from llm_judge import LLMJudge
from arch_scorer import ArchScorer
from metrics_calculator import MetricsCalculator


def _strip_provider_prefix(model: str) -> str:
    """Remove LiteLLM provider prefix, e.g. 'moonshot/kimi-k2.5' -> 'kimi-k2.5'."""
    return model.split("/", 1)[1] if "/" in model else model


def main():
    parser = argparse.ArgumentParser(description="Evaluate a single project.")
    parser.add_argument("--project", required=True, help="Project name, e.g. 4-by-4")
    parser.add_argument("--gt",   default=None, help="Ground-truth WSD/PUML path")
    parser.add_argument("--pred", default=None, help="Predicted PUML path")
    parser.add_argument("--prd",  default=None, help="PRD / input text path")
    parser.add_argument("--judge-api-key",  default=None)
    parser.add_argument("--judge-base-url", default=None,
                        help="OpenAI-compatible base URL, e.g. https://api.moonshot.cn/v1")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--no-cache", action="store_true",
                        help="Re-run LLM calls even if cached files exist")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM judge and scorer; compute structural metrics only")
    args = parser.parse_args()

    project = args.project

    # Default paths
    gt_path   = Path(args.gt)   if args.gt   else ROOT / "dataset" / "student_projects" / project / "ref.wsd"
    pred_path = Path(args.pred) if args.pred else ROOT / "run" / project / "component_diagram.puml"
    prd_path  = Path(args.prd)  if args.prd  else ROOT / "dataset" / "student_projects" / project / "input.txt"
    output_dir = EVAL_DIR / "outputs" / project
    output_dir.mkdir(parents=True, exist_ok=True)

    for p, label in [(gt_path, "Ground truth"), (pred_path, "Predicted PUML")]:
        if not p.exists():
            sys.exit(f"[Error] {label} not found: {p}")

    gt_code   = gt_path.read_text(encoding="utf-8")
    pred_code = pred_path.read_text(encoding="utf-8")
    prd_text  = prd_path.read_text(encoding="utf-8") if prd_path.exists() else ""

    # Parse both diagrams
    uml_parser = UMLParser()
    gt_parsed   = uml_parser.parse(gt_code)
    pred_parsed = uml_parser.parse(pred_code)
    print(f"[Parse] GT   — nodes={len(gt_parsed['nodes'])}  leafnodes={len(gt_parsed['leafnodes'])}  edges={len(gt_parsed['edges'])}")
    print(f"[Parse] Pred — nodes={len(pred_parsed['nodes'])}  leafnodes={len(pred_parsed['leafnodes'])}  edges={len(pred_parsed['edges'])}")

    # LLM config — strip provider prefix so OpenAI SDK gets a bare model name
    api_key  = args.judge_api_key  or os.environ.get("LLM_JUDGE_KEY") or os.environ.get("JUDGE_API_KEY") or os.environ.get("LLM_API_KEY",  "")
    base_url = args.judge_base_url or os.environ.get("LLM_JUDGE_URL") or os.environ.get("JUDGE_BASE_URL") or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    raw_model = args.judge_model or os.environ.get("JUDGE_MODEL") or os.environ.get("LLM_MODEL", "gpt-5.5")
    model = _strip_provider_prefix(raw_model)

    if not args.no_llm:
        print(f"[LLM]  model={model}  base_url={base_url or '(default OpenAI)'}")

    # ── Semantic alignment ─────────────────────────────────────────────────
    alignment_file = output_dir / "judge_alignment.json"
    if args.no_llm:
        alignment_result = {
            "matched_pairs": [],
            "unmatched_gt_nodes": gt_parsed["leafnodes"],
            "unmatched_predicted_nodes": pred_parsed["leafnodes"],
        }
    elif not args.no_cache and alignment_file.exists():
        print("[Alignment] Loading cached result…")
        alignment_result = json.loads(alignment_file.read_text(encoding="utf-8"))
    else:
        judge = LLMJudge(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            model_name=model,
        )
        alignment_result = judge.evaluate_alignment(
            prd_summary=prd_text[:3000],
            gt_nodes=gt_parsed["leafnodes"],
            predicted_nodes=pred_parsed["leafnodes"],
        )
        alignment_file.write_text(
            json.dumps(alignment_result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        n_matched = len(alignment_result.get("matched_pairs", []))
        print(f"[Alignment] {n_matched} matched pairs — saved to {alignment_file}")

    # ── Structural metrics ─────────────────────────────────────────────────
    calculator = MetricsCalculator()
    calculator.evaluate_project(
        project_name=project,
        gt_parsed=gt_parsed,
        pred_parsed=pred_parsed,
        alignment_data=alignment_result,
    )

    # ── LLM rubric scoring (4 dimensions) ─────────────────────────────────
    score_file = output_dir / "arch_score.json"
    dim_scores = {}
    if not args.no_llm:
        if not args.no_cache and score_file.exists():
            print("[Scoring] Loading cached result…")
            score_result = json.loads(score_file.read_text(encoding="utf-8"))
        else:
            # ArchScorer opens prompt.md relative to cwd
            orig_cwd = os.getcwd()
            os.chdir(EVAL_DIR)
            try:
                scorer = ArchScorer(
                    api_key=api_key,
                    base_url=base_url or "https://api.openai.com/v1",
                    model_name=model,
                )
                score_result = scorer.score(prd_text=prd_text, predicted_puml=pred_code)
            finally:
                os.chdir(orig_cwd)
            score_file.write_text(
                json.dumps(score_result, indent=2, ensure_ascii=False), encoding="utf-8"
            )

        dim_scores = ArchScorer.extract_scores(score_result)
        calculator.add_scores(project, dim_scores)
        print(f"[Scores] {dim_scores}")

    # ── Export ─────────────────────────────────────────────────────────────
    csv_path = output_dir / "eval_results.csv"
    calculator.export_to_csv(str(csv_path))
    print(f"\n[Done] Outputs in {output_dir}")


if __name__ == "__main__":
    main()
