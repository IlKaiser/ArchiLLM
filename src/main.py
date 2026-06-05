import os
import sys
import time
import csv

# Ensure the root of the project is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.prompt import DiagramPrompt

import argparse

def main():
    parser = argparse.ArgumentParser(description="Run UML component diagram pipeline over dataset projects.")
    parser.add_argument("--single-agent", action="store_true", help="Disable EffortRouter multi-agent delegation")
    parser.add_argument("--dataset-dir", default=None, help="Path to dataset projects directory (default: dataset/student_projects)")
    args = parser.parse_args()
    use_multi_agent = not args.single_agent
    _run_diagram_pipeline(use_multi_agent=use_multi_agent, dataset_dir=args.dataset_dir)

def _run_diagram_pipeline(use_multi_agent: bool = False, dataset_dir: str = None):
    from src.diagram_agent import run as run_diagram

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if dataset_dir is None:
        dataset_dir = os.path.join(base_dir, 'dataset', 'student_projects')

    MAX_TOTAL_COST = 50.0
    accumulated_cost = 0.0

    csv_file_path = os.path.join(base_dir, 'diagram_execution_report.csv')
    file_exists = os.path.exists(csv_file_path)

    with open(csv_file_path, mode='a', newline='') as csvfile:
        fieldnames = ['project_name', 'execution_time_seconds', 'cost', 'accumulated_cost']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

    if not os.path.exists(dataset_dir):
        print(f"Dataset directory not found at {dataset_dir}")
        return

    for project_name in sorted(os.listdir(dataset_dir)):
        if accumulated_cost >= MAX_TOTAL_COST:
            print(f"Cost threshold ({MAX_TOTAL_COST}) reached. Stopping.")
            break

        project_path = os.path.join(dataset_dir, project_name)
        if not os.path.isdir(project_path):
            continue

        input_file = os.path.join(project_path, 'input.txt')
        if not os.path.exists(input_file):
            print(f"Skipping {project_name}: input.txt not found.")
            continue

        print(f"{'='*50}")
        print(f"Running diagram pipeline for: {project_name}")
        print(f"{'='*50}")

        prompt = DiagramPrompt(title=project_name)
        start_time = time.time()
        try:
            cost = run_diagram(prompt=prompt, use_multi_agent=use_multi_agent)
            execution_time = time.time() - start_time
            accumulated_cost += cost

            with open(csv_file_path, mode='a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['project_name', 'execution_time_seconds', 'cost', 'accumulated_cost'])
                writer.writerow({
                    'project_name': project_name,
                    'execution_time_seconds': round(execution_time, 2),
                    'cost': round(cost, 4),
                    'accumulated_cost': round(accumulated_cost, 4),
                })

            print(f"Finished {project_name}. Time: {execution_time:.2f}s. Cost: {cost:.4f}. Accumulated: {accumulated_cost:.4f}")
        except Exception as e:
            print(f"Error running diagram pipeline for {project_name}: {e}")


if __name__ == "__main__":
    main()
