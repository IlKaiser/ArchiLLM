#!/usr/bin/env python3
"""
run_headless.py
---------------
Headless (non-UI) runner for the UML diagram generation pipeline.
Processes projects from MicroserviceDataset or dataset/student_projects.

Usage
-----
    # Process all projects in MicroserviceDataset
    python run_headless.py --dataset MicroserviceDataset

    # Process specific project with multi-agent
    python run_headless.py --dataset MicroserviceDataset --project spring-netflix-oss-microservices --multi-agent

    # Enable validator agent
    python run_headless.py --dataset MicroserviceDataset --validator

    # Process all with evaluation and visualization
    python run_headless.py --dataset MicroserviceDataset --eval --visualize

    # Set cost budget (stops when reached)
    python run_headless.py --dataset MicroserviceDataset --max-cost 25.0

    # Skip existing outputs (default behavior)
    python run_headless.py --dataset MicroserviceDataset --skip-existing

    # Force regeneration of all outputs
    python run_headless.py --dataset MicroserviceDataset --force

    # Generate charts from existing report
    python run_headless.py --dataset MicroserviceDataset --visualize --charts-dir ./charts

    # Only regenerate charts from existing CSV (no pipeline)
    python run_headless.py --charts-only --report headless_report.csv --charts-dir ./charts

    # Only run evaluation on existing outputs (no pipeline)
    python run_headless.py --eval-only --dataset MicroserviceDataset --output ./run

Environment
-----------
    LLM_MODEL, LLM_API_KEY, LLM_BASE_URL — primary LLM config
    SECONDARY_LLM_MODEL, SECONDARY_LLM_API_KEY — for multi-agent
    LLM_JUDGE_KEY, LLM_JUDGE_URL, JUDGE_MODEL — for evaluation
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for headless
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_EVAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Evaluation")
if _EVAL_DIR not in sys.path:
    sys.path.insert(0, _EVAL_DIR)

from src.prompt import DiagramPrompt, KNOWLEDGE_BASE


class RunProgress:
    """Atomically publish batch state for the static live dashboard."""

    def __init__(self, path: str, projects: list[str], args, model: str):
        self.path = Path(path).resolve()
        self.repo = Path(__file__).resolve().parent
        now = datetime.now(timezone.utc).isoformat()
        self.state = {
            "schema_version": 1,
            "run_id": self.path.stem,
            "phase": "microservice_generation",
            "status": "running",
            "pid": os.getpid(),
            "started_at": now,
            "updated_at": now,
            "finished_at": None,
            "dataset": str(args.dataset),
            "output": str(args.output),
            "report": str(args.report),
            "backend": args.local_backend or "cloud",
            "model": model,
            "total": len(projects),
            "projects": [
                {"name": name, "status": "pending", "time_seconds": None, "cost": None, "error": None}
                for name in projects
            ],
        }
        self.dashboard_live = bool(args.dashboard_live)
        self.write()

    def update_project(self, name: str, status: str, result: dict | None = None) -> None:
        entry = next(p for p in self.state["projects"] if p["name"] == name)
        entry["status"] = status
        if status == "running":
            entry["started_at"] = datetime.now(timezone.utc).isoformat()
        if result is not None:
            entry["time_seconds"] = result.get("time_seconds")
            entry["cost"] = result.get("cost")
            entry["error"] = result.get("error")
            entry["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.write()

    def finish(self) -> None:
        self.state["status"] = "failed" if any(
            p["status"] == "error" for p in self.state["projects"]
        ) else "complete"
        self.state["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.write()

    def write(self) -> None:
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temp_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        os.replace(temp_path, self.path)
        if self.dashboard_live:
            subprocess.run(
                [sys.executable, str(self.repo / "dashboard" / "generate.py")],
                cwd=self.repo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )


def plantuml_encode(text: str) -> str:
    """Encode PlantUML text for the public PlantUML server (same as app.py)."""
    import zlib
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    result = ""
    charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    for i in range(0, len(data), 3):
        b = data[i:i+3]
        if len(b) == 1:
            b = b + bytes(2)
        elif len(b) == 2:
            b = b + bytes(1)
        n = (b[0] << 16) | (b[1] << 8) | b[2]
        result += (charset[(n >> 18) & 0x3F] + charset[(n >> 12) & 0x3F] +
                   charset[(n >> 6) & 0x3F] + charset[n & 0x3F])
    return result


def render_puml_to_png(puml_path: Path) -> bool:
    """Download PNG from the PlantUML server and save next to the .puml file."""
    import urllib.request
    try:
        text = puml_path.read_text(encoding="utf-8")
        encoded = plantuml_encode(text)
        url = f"https://www.plantuml.com/plantuml/png/{encoded}"
        png_path = puml_path.with_suffix(".png")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ARCHILLMv2/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            png_path.write_bytes(resp.read())
        return True
    except Exception as e:
        # Some PlantUML CDN edges reject long encoded URLs from urllib while
        # accepting the identical URL through curl. Keep that interoperable
        # fallback so a valid diagram does not remain stuck with a stale PNG.
        try:
            subprocess.run(
                ["curl", "-fsSL", url, "-o", str(png_path)],
                check=True,
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            print(f"  ⚠ PNG render failed: {e}")
            return False


def setup_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Headless UML diagram generation pipeline runner"
    )
    parser.add_argument(
        "--dataset",
        default="MicroserviceDataset",
        help="Dataset directory name (default: MicroserviceDataset)",
    )
    parser.add_argument(
        "--project",
        help="Specific project name to process (if omitted, processes all)",
    )
    parser.add_argument(
        "--multi-agent",
        action="store_true",
        help="Enable EffortRouter multi-agent delegation",
    )
    parser.add_argument(
        "--validator",
        action="store_true",
        help="Enable Validation Agent (Agent 3)",
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run evaluation against ground truth and generate report",
    )
    parser.add_argument(
        "--output",
        default="./run",
        help="Output directory for generated diagrams (default: ./run)",
    )
    parser.add_argument(
        "--report",
        default="./headless_report.csv",
        help="CSV report file path (default: ./headless_report.csv)",
    )
    parser.add_argument(
        "--override",
        action="store_true",
        help="Override existing outputs (deprecated, use --force)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip projects that already have complete outputs (default: True)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if outputs exist (overrides --skip-existing)",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate visualization charts from results",
    )
    parser.add_argument(
        "--charts-only",
        action="store_true",
        help="Only generate charts from existing CSV report (no pipeline execution)",
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Only run evaluation on existing outputs (no pipeline execution)",
    )
    parser.add_argument(
        "--charts-dir",
        default="./charts",
        help="Directory for chart outputs (default: ./charts)",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=50.0,
        help="Maximum total cost budget in USD (default: 50.0)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "Number of projects to process concurrently, each in its own OS "
            "process (not a thread pool — run_pipeline() calls os.chdir() "
            "internally, which is process-wide, so threads would race on it). "
            "Default: 1 (sequential, unchanged behavior). Note: the --max-cost "
            "check only runs between completions, so with N workers spend can "
            "overshoot the budget by up to N-1 in-flight projects before new "
            "ones stop being started."
        ),
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default="all",
        help="Comma-separated list of metrics to compute: ged,structural,judge,all (default: all)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debug output for score calculation",
    )
    # ── Local model inference ──────────────────────────────────────────────
    parser.add_argument(
        "--local-backend",
        type=str,
        default=None,
        choices=["ollama", "huggingface", "hf", "tgi", "vllm"],
        help="Use a local model backend instead of a cloud API (ollama | huggingface/tgi/vllm)",
    )
    parser.add_argument(
        "--local-model",
        type=str,
        default=None,
        help=(
            "Local model name. "
            "Ollama: 'qwen2.5-coder:32b', 'llama3.1:70b', etc. "
            "HuggingFace/vLLM: 'mistralai/Mistral-7B-Instruct-v0.3', etc."
        ),
    )
    parser.add_argument(
        "--local-url",
        type=str,
        default=None,
        help=(
            "Base URL for the local inference server "
            "(default: http://localhost:11434 for Ollama, http://localhost:8080 for HF, "
            "http://localhost:8000 for vLLM)"
        ),
    )
    parser.add_argument(
        "--progress-file",
        default=None,
        help="Write atomic JSON run progress to this path",
    )
    parser.add_argument(
        "--dashboard-live",
        action="store_true",
        help="Regenerate dashboard/index.html whenever run progress changes",
    )
    return parser


def get_dataset_projects(dataset_dir: str) -> list[str]:
    """Get list of project folders in dataset directory."""
    base_path = Path(dataset_dir)
    if not base_path.exists():
        raise ValueError(f"Dataset directory not found: {dataset_dir}")
    
    projects = [
        p.name for p in base_path.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    return sorted(projects)


def prepare_project_input(
    project_name: str,
    dataset_dir: str,
    temp_input_dir: str
) -> bool:
    """
    Prepare input files for a project.
    For MicroserviceDataset: uses requirements.txt as input.txt
    For student_projects: uses existing input.txt
    Returns True if successful.
    """
    project_path = Path(dataset_dir) / project_name
    temp_path = Path(temp_input_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    
    # Check for MicroserviceDataset structure (requirements.txt + diagram.puml)
    req_file = project_path / "requirements.txt"
    diagram_file = project_path / "diagram.puml"
    
    if req_file.exists():
        # MicroserviceDataset format
        requirements = req_file.read_text(encoding="utf-8")
        
        # Create synthetic input.txt from requirements
        input_content = f"""# Project: {project_name}

## Requirements Document

{requirements}

## Task
Generate a UML component diagram for the microservices architecture described above.
"""
        (temp_path / "input.txt").write_text(input_content, encoding="utf-8")
        
        # Copy diagram.puml as ref.wsd if exists (for evaluation)
        if diagram_file.exists():
            (temp_path / "ref.wsd").write_text(diagram_file.read_text(encoding="utf-8"), encoding="utf-8")
        
        return True
    
    # Check for student_projects format (input.txt + ref.wsd)
    input_file = project_path / "input.txt"
    ref_file = project_path / "ref.wsd"
    
    if input_file.exists():
        shutil.copy2(input_file, temp_path / "input.txt")
        if ref_file.exists():
            shutil.copy2(ref_file, temp_path / "ref.wsd")
        
        # Check for DataMetrics.json (student_projects format)
        metrics_file = project_path / "DataMetrics.json"
        if metrics_file.exists():
            shutil.copy2(metrics_file, temp_path / "DataMetrics.json")
        
        return True
    
    return False


def check_output_complete(output_dir: str, project_name: str) -> bool:
    """Check if project has complete outputs (component_diagram.puml and architecture_summary.md)."""
    project_out = Path(output_dir) / project_name
    puml = project_out / "component_diagram.puml"
    summary = project_out / "architecture_summary.md"
    return puml.exists() and summary.exists()


def clean_output_dir(output_dir: str, project_name: str):
    """Remove all files from project output directory."""
    project_out = Path(output_dir) / project_name
    if project_out.exists():
        for f in project_out.iterdir():
            if f.is_file():
                f.unlink()


def run_pipeline(
    project_name: str,
    dataset_dir: str,
    output_dir: str,
    use_multi_agent: bool,
    use_validator: bool,
    skip_existing: bool,
    force: bool,
    local_llm_config: dict | None = None,
) -> dict:
    """Run the diagram pipeline for a single project."""
    from src.diagram_agent import run as run_diagram
    
    result = {
        "project": project_name,
        "status": "pending",
        "cost": 0.0,
        "time_seconds": 0.0,
        "error": None,
        "skipped": False,
    }
    
    # Check if already processed
    project_out = Path(output_dir) / project_name
    puml_path = project_out / "component_diagram.puml"
    summary_path = project_out / "architecture_summary.md"
    
    is_complete = check_output_complete(output_dir, project_name)
    
    if not force and skip_existing and is_complete:
        print(f"  ⚡ Skipping {project_name} — outputs exist (use --force to regenerate)")
        result["status"] = "skipped"
        result["skipped"] = True
        return result
    
    # If folder exists but incomplete, clean it
    if project_out.exists() and not is_complete:
        print(f"  🗑 Re-creating incomplete folder: {project_out}")
        clean_output_dir(output_dir, project_name)
    
    # Prepare temp input directory compatible with pipeline
    import tempfile
    
    temp_dataset_dir = tempfile.mkdtemp(prefix=f"dataset_{project_name}_")
    
    try:
        success = prepare_project_input(project_name, dataset_dir, temp_dataset_dir)
        if not success:
            result["status"] = "error"
            result["error"] = "No valid input files found"
            return result
        
        # Create synthetic student_projects structure
        temp_student_projects = Path(temp_dataset_dir) / "student_projects"
        temp_student_projects.mkdir(parents=True, exist_ok=True)
        
        project_temp_dir = temp_student_projects / project_name
        project_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files to expected location
        for fname in ["input.txt", "ref.wsd", "DataMetrics.json"]:
            src = Path(temp_dataset_dir) / fname
            if src.exists():
                shutil.copy2(src, project_temp_dir / fname)
        
        # Temporarily override dataset location
        original_cwd = os.getcwd()
        
        try:
            # We need to trick the pipeline into using our temp dataset
            # The pipeline looks for dataset/student_projects/{title}/input.txt
            os.chdir(temp_dataset_dir)
            
            # Create dataset symlink/dir structure
            (Path(temp_dataset_dir) / "dataset").mkdir(exist_ok=True)
            shutil.move(str(temp_student_projects), str(Path(temp_dataset_dir) / "dataset" / "student_projects"))
            
            # Change to temp dir so pipeline finds dataset/student_projects
            os.chdir(temp_dataset_dir)
            
            # Set env to use temp output dir
            original_run_dir = Path(original_cwd) / output_dir
            temp_run_dir = Path(temp_dataset_dir) / "run"
            
            print(f"  → Running pipeline for {project_name}...")
            start_time = time.time()
            
            diagram_prompt = DiagramPrompt(title=project_name)
            cost = run_diagram(
                prompt=diagram_prompt,
                use_multi_agent=use_multi_agent,
                use_validator=use_validator,
                local_llm_config=local_llm_config,
            )
            
            elapsed = time.time() - start_time
            
            # Copy results back to actual output dir
            result["status"] = "success"
            result["cost"] = cost
            result["time_seconds"] = elapsed
            
            project_output = temp_run_dir / project_name
            if temp_run_dir.exists() and project_output.exists():
                output_files = [f for f in project_output.iterdir() if f.is_file()]
                if output_files:
                    final_output = Path(original_cwd) / output_dir / project_name
                    final_output.mkdir(parents=True, exist_ok=True)
                    for f in output_files:
                        shutil.copy2(f, final_output / f.name)
                    print(f"  ✓ Completed in {elapsed:.2f}s, cost ${cost:.4f} ({len(output_files)} files copied)")
                    puml_final = final_output / "component_diagram.puml"
                    if puml_final.exists():
                        if render_puml_to_png(puml_final):
                            print(f"  ✓ PNG saved → {puml_final.with_suffix('.png')}")
                else:
                    result["status"] = "error"
                    result["error"] = "Pipeline produced empty output directory"
                    # Remove the stale empty folder so skip-existing won't treat it as done
                    final_output = Path(original_cwd) / output_dir / project_name
                    if final_output.exists() and not any(final_output.iterdir()):
                        final_output.rmdir()
            else:
                result["status"] = "error"
                result["error"] = "Pipeline did not produce output directory"
                # Remove the stale empty folder so skip-existing won't treat it as done
                final_output = Path(original_cwd) / output_dir / project_name
                if final_output.exists() and not any(final_output.iterdir()):
                    final_output.rmdir()
            
        finally:
            os.chdir(original_cwd)
            
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        print(f"  ✗ Failed: {exc}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup temp dir
        shutil.rmtree(temp_dataset_dir, ignore_errors=True)
    
    return result


def evaluate_project(
    project_name: str,
    dataset_dir: str,
    output_dir: str,
    llm_judge_key: str,
    llm_judge_url: str,
    judge_model: str,
    metrics: str = "all",
    verbose: bool = False,
) -> dict:
    """Run evaluation against ground truth.
    
    Args:
        metrics: Comma-separated list of metrics to compute:
            - ged: Graph Edit Distance only (no LLM)
            - structural: Node/Edge F1 with LLM alignment
            - judge: LLM judge scores (completeness, accuracy, etc.)
            - all: All metrics
    """
    import io, contextlib
    
    eval_result = {
        "structural": {},
        "judge": {},
        "score": {},
    }
    
    try:
        from uml_parser import UMLParser
        from metrics_calculator import MetricsCalculator
        from llm_judge import LLMJudge
        from arch_scorer import ArchScorer
        
        # Parse metrics selection
        metrics_set = set(m.lower() for m in metrics.split(","))
        compute_all = "all" in metrics_set
        compute_ged = compute_all or "ged" in metrics_set
        compute_structural = compute_all or "structural" in metrics_set
        compute_judge = compute_all or "judge" in metrics_set
        
        base_path = Path(dataset_dir) / project_name
        output_path = Path(output_dir) / project_name
        
        # Find ground truth (ref.wsd or diagram.puml)
        gt_path = base_path / "diagram.puml"
        if not gt_path.exists():
            gt_path = base_path / "ref.wsd"
        
        pred_path = output_path / "component_diagram.puml"
        
        if not gt_path.exists() or not pred_path.exists():
            return eval_result
        
        parser = UMLParser()
        gt_parsed = parser.parse(gt_path.read_text(encoding="utf-8"))
        pred_parsed = parser.parse(pred_path.read_text(encoding="utf-8"))
        
        # Phase 1: GED only (no LLM)
        if compute_ged and not compute_structural:
            calc = MetricsCalculator()
            no_llm_align = {
                "matched_pairs": [],
                "unmatched_gt_nodes": gt_parsed["leafnodes"],
                "unmatched_predicted_nodes": pred_parsed["leafnodes"],
            }
            
            with contextlib.redirect_stdout(io.StringIO()):
                calc.evaluate_project(
                    project_name=project_name,
                    gt_parsed=gt_parsed,
                    pred_parsed=pred_parsed,
                    alignment_data=no_llm_align,
                )
            
            if calc.results:
                eval_result["structural"] = calc.results[0]
            print(f"    ✓ GED computed: {eval_result['structural'].get('GED', 'N/A')}")
        
        # Phase 2 & 3: LLM evaluation (structural + judge)
        if llm_judge_key and (compute_structural or compute_judge):
            eval_out = Path(_EVAL_DIR) / "outputs" / project_name
            eval_out.mkdir(parents=True, exist_ok=True)
            
            j_cache = eval_out / "judge_alignment.json"
            s_cache = eval_out / "arch_score.json"
            
            # Get PRD text
            input_path = base_path / "requirements.txt"
            if not input_path.exists():
                input_path = base_path / "input.txt"
            
            prd_text = input_path.read_text(encoding="utf-8")[:3000] if input_path.exists() else ""
            
            # Phase 2: Structural metrics with LLM alignment
            if compute_structural:
                try:
                    judge = LLMJudge(
                        api_key=llm_judge_key,
                        base_url=llm_judge_url,
                        model_name=judge_model.split("/")[1] if "/" in judge_model else judge_model,
                    )
                    # Use service-level nodes for alignment (top-level boundaries)
                    # Falls back to leafnodes if no service nodes found
                    gt_nodes_for_align = gt_parsed.get("servicenodes") or gt_parsed["leafnodes"]
                    pred_nodes_for_align = pred_parsed.get("servicenodes") or pred_parsed["leafnodes"]
                    
                    # If majority of predicted service nodes are design-pattern names (Saga, CQRS, etc.)
                    # use all nodes (service boundaries + leaf nodes) for better matching
                    PATTERN_NAMES = {
                        "saga", "cqrs", "event sourcing", "api composition", "database per service",
                        "domain events", "api gateway pattern", "choreography", "orchestration"
                    }
                    pred_service_names = [n.split("::")[-1].lower() for n in pred_nodes_for_align]
                    pattern_count = sum(1 for n in pred_service_names if n in PATTERN_NAMES)
                    if pred_service_names and pattern_count / len(pred_service_names) >= 0.5:
                        # Majority are pattern names — include all non-db nodes (services + aliases)
                        all_pred = pred_parsed.get("nodes", [])
                        DB_KEYWORDS = ["db\n", "db\\n", "(relational)", "(document)", "(event store)", "event store", "read views", "database"]
                        pred_nodes_for_align = [
                            n for n in all_pred
                            if not any(kw in n.lower() for kw in DB_KEYWORDS)
                        ] or pred_parsed.get("leafnodes") or pred_nodes_for_align
                    
                    alignment = judge.evaluate_alignment(
                        prd_summary=prd_text,
                        gt_nodes=gt_nodes_for_align,
                        predicted_nodes=pred_nodes_for_align,
                    )
                    align_usage = alignment.pop("_usage", None)
                    if align_usage:
                        align_tokens = align_usage.get("total_tokens", 0)
                        eval_result["eval_cost"] = eval_result.get("eval_cost", 0.0) + align_tokens / 1_000_000 * 30.0
                        print(f"    ✓ LLM alignment computed ({align_usage['total_tokens']} tokens, ~${eval_result['eval_cost']:.4f})")
                    else:
                        print(f"    ✓ LLM alignment computed")
                    j_cache.write_text(json.dumps(alignment, indent=2, ensure_ascii=False), encoding="utf-8")
                    
                    # Debug output
                    if verbose:
                        gt_edges = gt_parsed.get("edges", [])
                        pred_edges = pred_parsed.get("edges", [])
                        matched_pairs = alignment.get("matched_pairs", [])
                        unmatched_gt = alignment.get("unmatched_gt_nodes", [])
                        unmatched_pred = alignment.get("unmatched_predicted_nodes", [])
                        
                        print(f"      [DEBUG] GT nodes sent:   {gt_nodes_for_align}")
                        print(f"      [DEBUG] Pred nodes sent: {pred_nodes_for_align}")
                        print(f"      [DEBUG] GT edges: {len(gt_edges)}, Pred edges: {len(pred_edges)}")
                        print(f"      [DEBUG] Matched pairs ({len(matched_pairs)}):")
                        for pair in matched_pairs:
                            if isinstance(pair, dict):
                                print(f"        GT={pair.get('gt_nodes')} ↔ Pred={pair.get('predicted_nodes')} boundary={'✓' if pair.get('is_boundary_correct') else '✗'}")
                        print(f"      [DEBUG] Unmatched GT ({len(unmatched_gt)}): {unmatched_gt}")
                        print(f"      [DEBUG] Unmatched Pred ({len(unmatched_pred)}): {unmatched_pred}")
                    
                    # Re-run metrics with alignment
                    calc2 = MetricsCalculator()
                    with contextlib.redirect_stdout(io.StringIO()):
                        calc2.evaluate_project(
                            project_name=project_name,
                            gt_parsed=gt_parsed,
                            pred_parsed=pred_parsed,
                            alignment_data=alignment,
                        )
                    
                    if calc2.results:
                        eval_result["structural"] = calc2.results[0]
                        struct = calc2.results[0]
                        node_f1 = struct.get('Node_F1')
                        edge_f1 = struct.get('Edge_F1')
                        ged = struct.get('GED')
                        boundary = struct.get('Boundary_Accuracy')
                        node_f1_str = f"{node_f1:.3f}" if node_f1 is not None else 'N/A'
                        edge_f1_str = f"{edge_f1:.3f}" if edge_f1 is not None else 'N/A'
                        print(f"    ✓ Structural metrics: Node_F1={node_f1_str}, Edge_F1={edge_f1_str}")
                        
                        if verbose:
                            print(f"      [DEBUG] Node_F1={node_f1}, Edge_F1={edge_f1}, GED={ged}, Boundary_Accuracy={boundary}")
                            # Node precision/recall (1 TP per matched pair)
                            node_tp = sum(1 for p in matched_pairs if isinstance(p, dict) and p.get("predicted_nodes"))
                            node_fp = len(unmatched_pred)
                            node_fn = len(unmatched_gt)
                            node_prec = node_tp / (node_tp + node_fp) if (node_tp + node_fp) > 0 else 0
                            node_rec = node_tp / (node_tp + node_fn) if (node_tp + node_fn) > 0 else 0
                            print(f"      [DEBUG] Node TP={node_tp}, FP={node_fp}, FN={node_fn} → Prec={node_prec:.3f}, Rec={node_rec:.3f}")
                            print(f"      [DEBUG] Edge Precision={struct.get('Edge_Precision')}, Recall={struct.get('Edge_Recall')}")
                    else:
                        print(f"    ⚠ No structural metrics with alignment")
                except Exception as exc:
                    print(f"    ⚠ LLM alignment failed: {exc}")
            
            # Phase 3: ArchScorer (judge scores)
            if compute_judge:
                try:
                    scorer = ArchScorer(
                        api_key=llm_judge_key,
                        base_url=llm_judge_url,
                        model_name=judge_model.split("/")[1] if "/" in judge_model else judge_model,
                    )
                    score_res = scorer.score(prd_text=prd_text, predicted_puml=pred_path.read_text(encoding="utf-8"))
                    
                    if score_res:
                        score_usage = score_res.pop("_usage", None)
                        if score_usage:
                            score_tokens = score_usage.get("total_tokens", 0)
                            eval_result["eval_cost"] = eval_result.get("eval_cost", 0.0) + score_tokens / 1_000_000 * 15.0
                        s_cache.write_text(json.dumps(score_res, indent=2, ensure_ascii=False), encoding="utf-8")
                        eval_result["score"] = score_res
                        eval_result["judge"] = ArchScorer.extract_scores(score_res)
                        judge_scores = eval_result["judge"]
                        total_eval_cost = eval_result.get('eval_cost', 0.0)
                        print(f"    ✓ Judge scores: Complete={judge_scores.get('Score_Completeness', 'N/A')}, Accurate={judge_scores.get('Score_Accuracy', 'N/A')} | Eval cost so far: ~${total_eval_cost:.4f}")
                    else:
                        print(f"    ⚠ ArchScorer returned no results")
                except Exception as exc:
                    print(f"    ⚠ ArchScorer failed: {exc}")
        
    except Exception as exc:
        print(f"  ⚠ Evaluation error: {exc}")
        import traceback
        traceback.print_exc()
    
    return eval_result


def write_csv_report(results: list[dict], report_path: str, mode: str = "a"):
    """Write results to CSV report with accumulated cost/time tracking.

    When mode='w' (rewrite), existing per-project data is read first and
    merged with incoming results so that a partial metrics run (e.g.
    --metrics judge) never blanks out columns it did not compute.

    Args:
        mode: "a" to append (default), "w" to overwrite/merge
    """
    fieldnames = [
        "project", "status", "time_seconds", "accumulated_time",
        "cost", "accumulated_cost", "eval_time_seconds", "eval_cost",
        "node_f1", "edge_f1", "ged", "boundary_accuracy",
        "completeness", "accuracy", "rationality", "readability",
        "error",
    ]

    # Load existing CSV rows so we can merge rather than overwrite
    existing: dict[str, dict] = {}
    report_file = Path(report_path)
    if report_file.exists():
        with open(report_path, "r", newline="") as f:
            for row in csv.DictReader(f):
                existing[row["project"]] = row

    file_exists = report_file.exists() and mode == "a"

    # Calculate running totals
    accumulated_cost = 0.0
    accumulated_time = 0.0

    with open(report_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists or mode == "w":
            writer.writeheader()

        for r in results:
            # Update running totals
            accumulated_cost += r.get("cost", 0)
            accumulated_time += r.get("time_seconds", 0) + r.get("eval_time_seconds", 0)

            # Start from the existing CSV row for this project (if any)
            prev = existing.get(r["project"], {})

            # eval_cost may come from the result dict or from the evaluation sub-dict
            eval_cost_val = r.get("eval_cost") or r.get("evaluation", {}).get("eval_cost", 0.0) or 0.0
            row = {
                "project": r["project"],
                "status": r["status"],
                "time_seconds": f"{r.get('time_seconds', 0):.2f}",
                "accumulated_time": f"{accumulated_time:.2f}",
                "cost": f"{r.get('cost', 0):.4f}",
                "accumulated_cost": f"{accumulated_cost:.4f}",
                "eval_time_seconds": f"{r.get('eval_time_seconds', 0):.2f}",
                "eval_cost": f"{eval_cost_val:.4f}" if eval_cost_val else prev.get("eval_cost", ""),
                "error": r.get("error", ""),
            }

            # Merge evaluation metrics: new value wins; fall back to existing CSV value
            eval_data = r.get("evaluation", {})
            struct = eval_data.get("structural", {})
            judge = eval_data.get("judge", {})

            def _fmt_float(val, decimals=3):
                return f"{val:.{decimals}f}" if val is not None else ""

            row["node_f1"]           = _fmt_float(struct.get("Node_F1"))           or prev.get("node_f1", "")
            row["edge_f1"]           = _fmt_float(struct.get("Edge_F1"))           or prev.get("edge_f1", "")
            row["ged"]               = _fmt_float(struct.get("GED"))               or prev.get("ged", "")
            row["boundary_accuracy"] = _fmt_float(struct.get("Boundary_Accuracy")) or prev.get("boundary_accuracy", "")
            row["completeness"]  = str(judge.get("Score_Completeness", "")) or prev.get("completeness", "")
            row["accuracy"]      = str(judge.get("Score_Accuracy",      "")) or prev.get("accuracy",      "")
            row["rationality"]   = str(judge.get("Score_Rationality",   "")) or prev.get("rationality",   "")
            row["readability"]   = str(judge.get("Score_Readability",   "")) or prev.get("readability",   "")

            writer.writerow(row)

    print(f"\nReport written to: {report_path}")


def read_csv_report(report_path: str) -> list[dict]:
    """Read results from existing CSV report."""
    results = []
    path = Path(report_path)
    
    if not path.exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        return results
    
    with open(report_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert CSV strings back to appropriate types
            result = {
                "project": row.get("project", ""),
                "status": row.get("status", "error"),
                "time_seconds": float(row.get("time_seconds", 0) or 0),
                "cost": float(row.get("cost", 0) or 0),
                "error": row.get("error", ""),
            }
            
            # Add evaluation metrics if present in CSV
            evaluation = {}
            structural = {}
            judge = {}
            
            if row.get("node_f1"):
                structural["Node_F1"] = float(row["node_f1"])
            if row.get("edge_f1"):
                structural["Edge_F1"] = float(row["edge_f1"])
            if row.get("ged"):
                structural["GED"] = float(row["ged"])
            if row.get("boundary_accuracy"):
                structural["Boundary_Accuracy"] = float(row["boundary_accuracy"])
            
            if row.get("completeness"):
                try:
                    judge["Score_Completeness"] = int(row["completeness"])
                except ValueError:
                    pass
            if row.get("accuracy"):
                try:
                    judge["Score_Accuracy"] = int(row["accuracy"])
                except ValueError:
                    pass
            if row.get("rationality"):
                try:
                    judge["Score_Rationality"] = int(row["rationality"])
                except ValueError:
                    pass
            if row.get("readability"):
                try:
                    judge["Score_Readability"] = int(row["readability"])
                except ValueError:
                    pass
            
            if structural:
                evaluation["structural"] = structural
            if judge:
                evaluation["judge"] = judge
            if evaluation:
                result["evaluation"] = evaluation
            
            results.append(result)
    
    print(f"Loaded {len(results)} records from {report_path}")
    return results


def process_one_project(
    project: str,
    dataset_path: Path,
    args,
    llm_judge_key: str,
    llm_judge_url: str,
    judge_model: str,
    local_llm_config: dict | None,
) -> dict:
    """Generate (or skip) + evaluate a single project. Pulled out of main()'s
    loop so both the sequential and --workers > 1 paths call the same code."""
    skip_existing = args.skip_existing and not args.force and not args.override
    force = args.force or args.override

    result = run_pipeline(
        project_name=project,
        dataset_dir=str(dataset_path),
        output_dir=args.output,
        use_multi_agent=args.multi_agent,
        use_validator=args.validator,
        skip_existing=skip_existing,
        force=force,
        local_llm_config=local_llm_config,
    )

    if result["status"] in ("success", "skipped"):
        puml_path = Path(args.output) / project / "component_diagram.puml"
        png_path = puml_path.with_suffix(".png")
        if puml_path.exists():
            needs_render = (
                not png_path.exists()
                or puml_path.stat().st_mtime > png_path.stat().st_mtime
            )
            if needs_render:
                if render_puml_to_png(puml_path):
                    print(f"  ✓ PNG updated → {png_path}")

    if args.eval and result["status"] in ("success", "skipped"):
        print(f"  → Running evaluation...")
        eval_data = evaluate_project(
            project_name=project,
            dataset_dir=str(dataset_path),
            output_dir=args.output,
            llm_judge_key=llm_judge_key,
            llm_judge_url=llm_judge_url,
            judge_model=judge_model,
            metrics=args.metrics,
            verbose=args.verbose,
        )
        result["evaluation"] = eval_data
        if eval_data.get("eval_cost"):
            result["eval_cost"] = eval_data["eval_cost"]

    return result


def _run_one_project_in_subprocess(
    i: int,
    project: str,
    dataset_path: Path,
    args,
    llm_judge_key: str,
    llm_judge_url: str,
    judge_model: str,
    local_llm_config: dict | None,
) -> tuple[int, str, str, dict]:
    """--workers > 1 entry point, run by ProcessPoolExecutor. Each project
    gets its own OS process (own PID, own CWD) rather than a thread, because
    process_one_project()'s run_pipeline() calls os.chdir() internally —
    that's process-wide, so threads sharing one process would stomp on each
    other's working directory mid-run. Separate processes sidestep that
    entirely. Output is captured to a temp file (redirect_stdout is safe here
    since each process only has one top-level caller) and read back so the
    parent can print each project's full log as one uninterrupted block.
    """
    import contextlib
    import os
    import tempfile

    log_path = Path(tempfile.gettempdir()) / f"arthur_worker_{os.getpid()}_{i}.log"
    with open(log_path, "w", encoding="utf-8") as f, contextlib.redirect_stdout(f):
        result = process_one_project(
            project, dataset_path, args, llm_judge_key, llm_judge_url, judge_model, local_llm_config,
        )
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    log_path.unlink(missing_ok=True)
    return i, project, log_text, result


def main():
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # Handle charts-only mode: generate charts from existing CSV without running pipeline
    if args.charts_only:
        print(f"{'═'*60}")
        print(f"Charts-Only Mode: Generating visualizations from existing report")
        print(f"{'═'*60}")
        
        results = read_csv_report(args.report)
        if not results:
            print(f"No data found in {args.report}", file=sys.stderr)
            sys.exit(1)
        
        generate_charts(results, args.charts_dir)
        print(f"\n✓ Charts generated successfully")
        sys.exit(0)
    
    # Handle eval-only mode: run evaluation on existing outputs
    if args.eval_only:
        print(f"{'═'*60}")
        print(f"Eval-Only Mode: Running evaluation on existing outputs")
        print(f"{'═'*60}")
        
        dataset_path = Path(args.dataset)
        if not dataset_path.exists():
            print(f"Error: Dataset directory not found: {dataset_path}", file=sys.stderr)
            sys.exit(1)
        
        # Get projects to process
        if args.project:
            projects = [args.project]
        else:
            projects = get_dataset_projects(str(dataset_path))
        
        if not projects:
            print("No projects found in dataset", file=sys.stderr)
            sys.exit(1)
        
        # LLM Judge config for evaluation
        llm_judge_key = os.getenv("LLM_JUDGE_KEY") or os.getenv("LLM_API_KEY")
        llm_judge_url = os.getenv("LLM_JUDGE_URL", "https://api.openai.com/v1")
        judge_model = os.getenv("JUDGE_MODEL", "gpt-5.6-luna")

        print(f"Dataset: {dataset_path}")
        print(f"Projects: {len(projects)}")
        print(f"Output dir: {args.output}")
        print(f"{'═'*60}\n")
        
        # Load existing results from CSV
        results = read_csv_report(args.report)
        existing_projects = {r["project"]: r for r in results}
        
        total_eval_time = 0.0
        total_eval_cost = 0.0
        
        for i, project in enumerate(projects):
            print(f"\n[{i+1}/{len(projects)}] Evaluating: {project}")
            
            # Check if project has existing result
            if project not in existing_projects:
                print(f"  ⚠ No existing record for {project}, skipping")
                continue
            
            result = existing_projects[project]
            
            # Track evaluation time
            eval_start = time.time()
            
            # Run evaluation
            eval_data = evaluate_project(
                project_name=project,
                dataset_dir=str(dataset_path),
                output_dir=args.output,
                llm_judge_key=llm_judge_key,
                llm_judge_url=llm_judge_url,
                judge_model=judge_model,
                metrics=args.metrics,
                verbose=args.verbose,
            )
            eval_time = time.time() - eval_start
            
            result["evaluation"] = eval_data
            result["eval_time_seconds"] = round(eval_time, 2)
            if eval_data.get("eval_cost"):
                result["eval_cost"] = eval_data["eval_cost"]
                total_eval_cost += eval_data["eval_cost"]
            total_eval_time += eval_time
            
            # Update status to reflect evaluation was performed
            if result.get("status") == "skipped":
                result["status"] = "evaluated"
            
            print(f"  → Evaluation took {eval_time:.1f}s | Running eval totals: {total_eval_time:.1f}s, ~${total_eval_cost:.4f}")
            
            # Update in results list
            for idx, r in enumerate(results):
                if r["project"] == project:
                    results[idx] = result
                    break
            
            # Brief pause between evaluations
            if i < len(projects) - 1:
                time.sleep(1)
        
        # Write updated report (overwrite mode to avoid duplicates)
        write_csv_report(results, args.report, mode="w")
        
        # Generate visualizations if requested
        if args.visualize:
            generate_charts(results, args.charts_dir)
        
        print(f"\n{'═'*60}")
        print(f"✓ Evaluation complete")
        print(f"  Total eval time: {total_eval_time:.1f}s ({total_eval_time/60:.1f} min)")
        print(f"  Total eval cost: ~${total_eval_cost:.4f}")
        print(f"  Report updated: {args.report}")
        print(f"{'═'*60}")
        sys.exit(0)
    
    # Validate environment
    if not args.local_backend and not os.getenv("LLM_API_KEY"):
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Dataset directory not found: {dataset_path}", file=sys.stderr)
        sys.exit(1)
    
    # Get projects to process
    if args.project:
        projects = [args.project]
    else:
        projects = get_dataset_projects(str(dataset_path))
    
    if not projects:
        print("No projects found in dataset", file=sys.stderr)
        sys.exit(1)
    
    print(f"{'═'*60}")
    print(f"Headless Pipeline Runner")
    print(f"{'═'*60}")
    print(f"Dataset: {dataset_path}")
    print(f"Projects: {len(projects)}")
    print(f"Multi-agent: {args.multi_agent}")
    print(f"Validator: {args.validator}")
    print(f"Evaluation: {args.eval}")
    print(f"{'═'*60}\n")
    
    # LLM Judge config for evaluation
    llm_judge_key = os.getenv("LLM_JUDGE_KEY") or os.getenv("LLM_API_KEY")
    llm_judge_url = os.getenv("LLM_JUDGE_URL", "https://api.openai.com/v1")
    judge_model = os.getenv("JUDGE_MODEL", "gpt-5.6-luna")

    # Local model inference config (Ollama / HuggingFace TGI / vLLM)
    local_llm_config = None
    if args.local_backend:
        if not args.local_model:
            print("Error: --local-model is required when --local-backend is set", file=sys.stderr)
            sys.exit(1)
        from src.local_llm import get_local_llm_config, describe_local_config
        local_llm_config = get_local_llm_config(
            backend=args.local_backend,
            model=args.local_model,
            base_url=args.local_url,
        )
        print(f"{'═'*60}")
        print(f"⚡ LOCAL INFERENCE MODE")
        print(f"  Backend : {args.local_backend}")
        print(f"  {describe_local_config(local_llm_config)}")
        print(f"  (native tool-calling enabled, temperature=0.0)")
        print(f"{'═'*60}\n")

    progress = None
    if args.progress_file or args.dashboard_live:
        progress_path = args.progress_file or "dashboard/run_progress/current.json"
        active_model = args.local_model if args.local_backend else os.getenv("LLM_MODEL", "")
        progress = RunProgress(progress_path, projects, args, active_model)

    results = []
    total_cost = 0.0
    total_eval_cost = 0.0
    accumulated_time = 0.0

    print(f"Budget: ${args.max_cost:.2f} max cost\n")

    def record(i: int, project: str, result: dict) -> None:
        nonlocal total_cost, total_eval_cost, accumulated_time
        results.append(result)
        total_cost += result.get("cost", 0)
        accumulated_time += result.get("time_seconds", 0)
        if result.get("eval_cost"):
            total_eval_cost += result["eval_cost"]
        eval_cost_str = f" | eval ~${total_eval_cost:.4f}" if total_eval_cost else ""
        print(f"  → Running totals: ${total_cost:.4f} pipeline cost | {accumulated_time:.1f}s time{eval_cost_str}")
        if progress:
            progress.update_project(project, result.get("status", "error"), result)

    if args.workers <= 1:
        for i, project in enumerate(projects):
            if total_cost >= args.max_cost:
                print(f"\n⚠ Cost budget (${args.max_cost:.2f}) reached. Stopping.")
                break
            print(f"\n[{i+1}/{len(projects)}] Processing: {project} (accumulated: ${total_cost:.4f})")
            if progress:
                progress.update_project(project, "running")
            result = process_one_project(
                project, dataset_path, args, llm_judge_key, llm_judge_url, judge_model, local_llm_config,
            )
            record(i, project, result)
            if i < len(projects) - 1:
                time.sleep(1)
    else:
        # Concurrent path: one OS process per project, not a thread pool.
        # process_one_project()'s run_pipeline() calls os.chdir() internally,
        # which is process-wide — concurrent threads sharing one process would
        # race on that and corrupt each other's relative-path resolution
        # (confirmed: this broke DataMetrics.json lookups under threading).
        # Separate processes each get their own CWD, so this is safe.
        import concurrent.futures

        print(f"⚡ Running with {args.workers} parallel workers (separate processes)\n")

        project_iter = iter(enumerate(projects))
        budget_hit = False
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
            in_flight: dict = {}

            def submit_next() -> bool:
                try:
                    i, project = next(project_iter)
                except StopIteration:
                    return False
                print(f"\n[{i+1}/{len(projects)}] Submitting: {project} (accumulated: ${total_cost:.4f})")
                if progress:
                    progress.update_project(project, "running")
                fut = pool.submit(
                    _run_one_project_in_subprocess,
                    i, project, dataset_path, args, llm_judge_key, llm_judge_url, judge_model, local_llm_config,
                )
                in_flight[fut] = project
                return True

            for _ in range(args.workers):
                if not submit_next():
                    break

            while in_flight:
                done, _ = concurrent.futures.wait(in_flight.keys(), return_when=concurrent.futures.FIRST_COMPLETED)
                for fut in done:
                    in_flight.pop(fut)
                    i, project, log, result = fut.result()
                    print(f"\n{'─'*60}\n[{i+1}/{len(projects)}] {project} finished\n{'─'*60}")
                    print(log, end="")
                    record(i, project, result)
                    if total_cost >= args.max_cost:
                        if not budget_hit:
                            print(
                                f"\n⚠ Cost budget (${args.max_cost:.2f}) reached. "
                                f"Letting {len(in_flight)} in-flight project(s) finish; no new ones will start."
                            )
                        budget_hit = True
                    elif not budget_hit:
                        submit_next()

    # Summary
    print(f"\n{'═'*60}")
    print("Summary")
    print(f"{'═'*60}")
    
    success = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "error"]
    
    print(f"  Succeeded: {len(success)}")
    print(f"  Skipped:   {len(skipped)}")
    print(f"  Failed:    {len(failed)}")
    print(f"  ─────────────────────────────")
    print(f"  Total Time:      {accumulated_time:.1f}s ({accumulated_time/60:.1f} min)")
    print(f"  Pipeline Cost:   ${total_cost:.4f} (${args.max_cost - total_cost:.4f} remaining)")
    if total_eval_cost:
        print(f"  Eval Cost:       ~${total_eval_cost:.4f} (alignment + judge)")
    if total_cost >= args.max_cost:
        print(f"  ⚠ Budget exhausted")
    
    if failed:
        print(f"\nFailed projects:")
        for r in failed:
            print(f"  ✗ {r['project']}: {r.get('error', 'Unknown error')}")
    
    # Write report
    write_csv_report(results, args.report)

    if progress:
        progress.finish()
    
    # Generate visualizations if requested
    if args.visualize:
        generate_charts(results, args.charts_dir)


def generate_charts(results: list[dict], charts_dir: str):
    """Generate visualization charts from results."""
    if not HAS_MATPLOTLIB:
        print("\n⚠ matplotlib not installed. Install with: pip install matplotlib")
        return
    
    charts_path = Path(charts_dir)
    charts_path.mkdir(parents=True, exist_ok=True)
    
    # Filter to successful runs with evaluation data
    eval_results = [
        r for r in results 
        if r["status"] in ("success", "skipped") and "evaluation" in r
    ]
    
    if not eval_results:
        print("\n⚠ No evaluation data available for visualization")
        return
    
    print(f"\n{'═'*60}")
    print("Generating Charts")
    print(f"{'═'*60}")
    
    project_names = [r["project"][:20] for r in eval_results]  # Truncate long names
    
    # Extract metrics
    node_f1 = []
    edge_f1 = []
    ged = []
    boundary_acc = []
    completeness = []
    accuracy = []
    rationality = []
    readability = []
    costs = []
    times = []
    
    for r in eval_results:
        eval_data = r.get("evaluation", {})
        struct = eval_data.get("structural", {})
        judge = eval_data.get("judge", {})
        
        node_f1.append(struct.get("Node_F1", 0) or 0)
        edge_f1.append(struct.get("Edge_F1", 0) or 0)
        ged.append((struct.get("GED", 0) or 0) / 100)  # Normalize GED
        boundary_acc.append(struct.get("Boundary_Accuracy", 0) or 0)
        
        completeness.append(judge.get("Score_Completeness", 0) or 0)
        accuracy.append(judge.get("Score_Accuracy", 0) or 0)
        rationality.append(judge.get("Score_Rationality", 0) or 0)
        readability.append(judge.get("Score_Readability", 0) or 0)
        
        costs.append(r.get("cost", 0))
        times.append(r.get("time_seconds", 0))
    
    x = range(len(project_names))
    
    # Chart 1: Structural Metrics
    fig, ax = plt.subplots(figsize=(12, 6))
    width = 0.2
    ax.bar([i - 1.5*width for i in x], node_f1, width, label="Node F1", color="#3498db")
    ax.bar([i - 0.5*width for i in x], edge_f1, width, label="Edge F1", color="#2ecc71")
    ax.bar([i + 0.5*width for i in x], ged, width, label="GED (norm)", color="#e74c3c")
    ax.bar([i + 1.5*width for i in x], boundary_acc, width, label="Boundary Acc", color="#9b59b6")
    ax.set_xlabel("Project")
    ax.set_ylabel("Score")
    ax.set_title("Structural Metrics by Project")
    ax.set_xticks(x)
    ax.set_xticklabels(project_names, rotation=45, ha="right")
    ax.legend()
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(charts_path / "structural_metrics.png", dpi=150)
    plt.close()
    print(f"  ✓ structural_metrics.png")
    
    # Chart 2: LLM Judge Scores
    if any(completeness):  # Only if we have judge scores
        fig, ax = plt.subplots(figsize=(12, 6))
        width = 0.2
        ax.bar([i - 1.5*width for i in x], completeness, width, label="Completeness", color="#1abc9c")
        ax.bar([i - 0.5*width for i in x], accuracy, width, label="Accuracy", color="#f39c12")
        ax.bar([i + 0.5*width for i in x], rationality, width, label="Rationality", color="#e67e22")
        ax.bar([i + 1.5*width for i in x], readability, width, label="Readability", color="#34495e")
        ax.set_xlabel("Project")
        ax.set_ylabel("Score (0-5)")
        ax.set_title("LLM Judge Scores by Project")
        ax.set_xticks(x)
        ax.set_xticklabels(project_names, rotation=45, ha="right")
        ax.legend()
        ax.set_ylim(0, 5.5)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(charts_path / "judge_scores.png", dpi=150)
        plt.close()
        print(f"  ✓ judge_scores.png")
    
    # Chart 3: Cost & Time
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Cost chart
    colors = ["#27ae60" if c < 0.5 else "#f39c12" if c < 1.0 else "#e74c3c" for c in costs]
    ax1.bar(project_names, costs, color=colors)
    ax1.set_xlabel("Project")
    ax1.set_ylabel("Cost ($)")
    ax1.set_title("Pipeline Cost by Project")
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(axis="y", alpha=0.3)
    
    # Time chart
    ax2.bar(project_names, times, color="#3498db")
    ax2.set_xlabel("Project")
    ax2.set_ylabel("Time (seconds)")
    ax2.set_title("Pipeline Execution Time")
    ax2.tick_params(axis="x", rotation=45)
    ax2.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(charts_path / "cost_time.png", dpi=150)
    plt.close()
    print(f"  ✓ cost_time.png")
    
    # Chart 4: Summary Radar — structural + LLM judge (always all 7 axes)
    import math

    def _avg(lst):
        vals = [v for v in lst if v is not None]
        return sum(vals) / len(vals) if vals else 0.0

    # Only average judge scores from projects that actually have them (non-zero)
    judge_completeness = [v for v in completeness if v > 0]
    judge_accuracy     = [v for v in accuracy     if v > 0]
    judge_rationality  = [v for v in rationality  if v > 0]
    judge_readability  = [v for v in readability  if v > 0]
    has_judge = bool(judge_completeness)

    categories = [
        "Node F1", "Edge F1", "Boundary Acc",
        "Completeness", "Accuracy", "Rationality", "Readability"
    ]
    n_cat = len(categories)
    angles = [n / float(n_cat) * 2 * math.pi for n in range(n_cat)]
    angles += angles[:1]

    # Structural series (normalised 0-1)
    struct_vals = [
        _avg(node_f1),
        _avg(edge_f1),
        _avg(boundary_acc),
        0, 0, 0, 0,   # judge axes — structural trace shows 0 here
    ]
    # LLM Judge series (normalised 0-1 by dividing by max score 5)
    judge_vals = [
        0, 0, 0,       # structural axes — judge trace shows 0 here
        _avg(judge_completeness) / 5,
        _avg(judge_accuracy)     / 5,
        _avg(judge_rationality)  / 5,
        _avg(judge_readability)  / 5,
    ]
    # Combined series for annotation
    combined_vals = [
        _avg(node_f1),
        _avg(edge_f1),
        _avg(boundary_acc),
        _avg(judge_completeness) / 5,
        _avg(judge_accuracy)     / 5,
        _avg(judge_rationality)  / 5,
        _avg(judge_readability)  / 5,
    ]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))

    # Structural fill (blue)
    sv = struct_vals + struct_vals[:1]
    ax.plot(angles, sv, 'o-', linewidth=2, color="#3498db", label="Structural")
    ax.fill(angles, sv, alpha=0.20, color="#3498db")

    # LLM Judge fill (orange) — only if we have data
    if has_judge:
        jv = judge_vals + judge_vals[:1]
        ax.plot(angles, jv, 's-', linewidth=2, color="#e67e22", label="LLM Judge")
        ax.fill(angles, jv, alpha=0.20, color="#e67e22")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)

    # Value labels on every axis
    for angle, val, cat in zip(angles[:-1], combined_vals, categories):
        if val > 0:
            label_r = min(val + 0.09, 0.97)
            ax.text(angle, label_r, f"{val:.2f}",
                    ha="center", va="center", fontsize=9, fontweight="bold", color="#2c3e50")

    # Shade background sectors: structural (left half) vs judge (right half)
    ax.axvspan(0, 3 / n_cat * 2 * math.pi, alpha=0.03, color="#3498db")
    ax.axvspan(3 / n_cat * 2 * math.pi, 2 * math.pi, alpha=0.03, color="#e67e22")

    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=8, color="grey")
    ax.grid(color="grey", linestyle="--", linewidth=0.5, alpha=0.4)
    subtitle = f"(LLM Judge: {len(judge_completeness)}/{len(eval_results)} projects scored)" if has_judge else "(LLM Judge scores not yet available)"
    ax.set_title(f"Average Performance Across All Projects\n{subtitle}",
                 y=1.10, fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.tight_layout()
    plt.savefig(charts_path / "average_radar.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  ✓ average_radar.png")
    
    # Chart 5: Status distribution (pie chart)
    status_counts = {"success": 0, "skipped": 0, "error": 0}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = {"success": "#2ecc71", "skipped": "#f39c12", "error": "#e74c3c"}
    labels = [f"{k}: {v}" for k, v in status_counts.items() if v > 0]
    sizes = [v for v in status_counts.values() if v > 0]
    pie_colors = [colors.get(k, "#95a5a6") for k, v in status_counts.items() if v > 0]
    
    ax.pie(sizes, labels=labels, colors=pie_colors, autopct="%1.1f%%", startangle=90)
    ax.set_title("Pipeline Execution Status Distribution")
    plt.tight_layout()
    plt.savefig(charts_path / "status_distribution.png", dpi=150)
    plt.close()
    print(f"  ✓ status_distribution.png")
    
    # Chart 6: Accumulated Cost & Time Trends
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    x_pos = range(len(project_names))
    
    # Calculate accumulated values
    acc_costs = []
    acc_times = []
    running_cost = 0.0
    running_time = 0.0
    for c, t in zip(costs, times):
        running_cost += c
        running_time += t
        acc_costs.append(running_cost)
        acc_times.append(running_time)
    
    # Accumulated cost trend
    ax1.fill_between(x_pos, acc_costs, alpha=0.3, color="#e74c3c")
    ax1.plot(x_pos, acc_costs, 'o-', linewidth=2, color="#e74c3c", markersize=6)
    ax1.set_xlabel("Project")
    ax1.set_ylabel("Accumulated Cost ($)")
    ax1.set_title("Accumulated Cost Trend")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(project_names, rotation=45, ha="right")
    ax1.grid(axis="y", alpha=0.3)
    
    # Accumulated time trend
    ax2.fill_between(x_pos, acc_times, alpha=0.3, color="#3498db")
    ax2.plot(x_pos, acc_times, 'o-', linewidth=2, color="#3498db", markersize=6)
    ax2.set_xlabel("Project")
    ax2.set_ylabel("Accumulated Time (seconds)")
    ax2.set_title("Accumulated Time Trend")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(project_names, rotation=45, ha="right")
    ax2.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(charts_path / "accumulated_trends.png", dpi=150)
    plt.close()
    print(f"  ✓ accumulated_trends.png")
    
    print(f"\nCharts saved to: {charts_path}")


if __name__ == "__main__":
    main()
