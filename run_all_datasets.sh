#!/usr/bin/env bash
# Run the full ARCHI pipeline (diagram generation + evaluation + modifiability
# analysis) across every dataset available in the repo, using DeepSeek V4.1
# Flash as the primary LLM:
#   - dataset/student_projects
#   - dataset/open_source_projects
#   - MicroserviceDataset
#
# Each dataset's artifacts (diagrams, architecture.json, CSV report, and for
# student_projects the modifiability reports) are kept in their own folder
# under RESULTS_ROOT so nothing from one dataset overwrites another, and the
# script prints every CSV/JSON report it produces at the end.
#
# Note: dataset/pention/ is raw source material (PDF/xlsx/input.txt directly
# at the top level, not one-folder-per-project), not a pipeline-ready dataset
# dir — it's already represented as dataset/student_projects/PENTION.
set -euo pipefail

cd "$(dirname "$0")"

# deepseek/deepseek-flash = DeepSeek V4.1 Flash (see .env's LLM_MODEL default).
# LLM_API_KEY must be a valid DeepSeek API key when using this model; leave
# LLM_BASE_URL unset so LiteLLM resolves DeepSeek's endpoint itself. Override
# by exporting LLM_MODEL before calling this script if you want a different one
# (e.g. moonshot/kimi-k2.5).
export LLM_MODEL="${LLM_MODEL:-deepseek/deepseek-flash}"

# Projects processed concurrently per dataset (thread pool; I/O-bound LLM
# calls — see run_headless.py --workers). Override with WORKERS=N.
WORKERS="${WORKERS:-4}"

RESULTS_ROOT="results"
REPORTS_DIR="${RESULTS_ROOT}/reports"
mkdir -p "${REPORTS_DIR}"

echo "Using LLM_MODEL=${LLM_MODEL}, WORKERS=${WORKERS}"

# --- Stage 1: diagram generation + structural/LLM-judge evaluation --------
DATASETS=(
  "dataset/student_projects:student_projects"
  "dataset/open_source_projects:open_source_projects"
  "MicroserviceDataset:microservice_dataset"
)

for entry in "${DATASETS[@]}"; do
  ds="${entry%%:*}"
  name="${entry##*:}"
  out_dir="${RESULTS_ROOT}/${name}"
  report="${REPORTS_DIR}/${name}_report.csv"
  mkdir -p "${out_dir}"
  echo
  echo "=== Generating + evaluating diagrams for ${ds} -> ${out_dir} ==="
  python run_headless.py \
    --dataset "${ds}" \
    --output "${out_dir}" \
    --report "${report}" \
    --eval --metrics all --visualize --skip-existing \
    --workers "${WORKERS}"
done

# --- Stage 2: modifiability analysis (student_projects only) --------------
# Evaluation/modifiability.py's CLI hardcodes dataset_dir=dataset/student_projects
# and run_dir="run" with no override flags, so it can't point at our separated
# results/ folders out of the box. We call Evaluation.modifiability.run()
# directly instead, pointed at results/student_projects (this run's Stage 1
# output), so architecture.json / component_diagram.puml resolve correctly.
echo
echo "=== Running modifiability analysis for dataset/student_projects ==="
MOD_RUN_DIR="${RESULTS_ROOT}/student_projects"
for project_dir in dataset/student_projects/*/; do
  project="$(basename "${project_dir}")"
  echo "--- modifiability: ${project} ---"
  python -c "
import sys
from Evaluation.modifiability import run
run(sys.argv[1], run_dir=sys.argv[2], dataset_dir='dataset/student_projects')
" "${project}" "${MOD_RUN_DIR}"
done

# --- Output every report produced -----------------------------------------
echo
echo "=========================================================="
echo "REPORTS (${REPORTS_DIR})"
echo "=========================================================="
for csv in "${REPORTS_DIR}"/*.csv; do
  [ -e "${csv}" ] || continue
  echo
  echo "--- ${csv} ---"
  if command -v column >/dev/null 2>&1; then
    column -t -s, "${csv}"
  else
    cat "${csv}"
  fi
done

echo
echo "=========================================================="
echo "MODIFIABILITY SCORES (${MOD_RUN_DIR}/<project>/modifiability/report.json)"
echo "=========================================================="
python -c "
import json
from pathlib import Path

mod_run_dir = Path('${MOD_RUN_DIR}')
for report_path in sorted(mod_run_dir.glob('*/modifiability/report.json')):
    r = json.loads(report_path.read_text(encoding='utf-8'))
    print(f\"{r['project']:<20} modifiability_score={r['modifiability_score']:.4f}  \"
          f\"n_scenarios={r['n_scenarios']}  cost=\${r['total_cost_usd']:.4f}\")
"

echo
echo "All datasets processed. Results under ${RESULTS_ROOT}/"
