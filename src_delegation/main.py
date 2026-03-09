import os
import sys
import time
import csv

# Ensure the root of the project is in the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.prompt import Prompt
from src_delegation.agent import run

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    projects_dir = os.path.join(base_dir, 'projects')
    # Maximum total cost across all runs
    MAX_TOTAL_COST = 50.0
    accumulated_cost = 0.0
    
    # List of subfolders to skip
    SKIP_LIST = ["hfte", "rentanorchid", "gasstation", "donationbank",
                 "alphainsurance", "tuxme", "kinepolis"]
    
    # Setup CSV logging
    csv_file_path = os.path.join(base_dir, 'execution_report.csv')
    file_exists = os.path.exists(csv_file_path)
    
    with open(csv_file_path, mode='a', newline='') as csvfile:
        fieldnames = ['project_name', 'execution_time_seconds', 'cost', 'accumulated_cost']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
    
    if not os.path.exists(projects_dir):
        print(f"Projects directory not found at {projects_dir}")
        return

    # Iterate over each subfolder in the projects folder
    for project_name in os.listdir(projects_dir):
        if project_name in SKIP_LIST:
            print(f"Skipping {project_name}: found in SKIP_LIST.")
            continue
            
        if accumulated_cost >= MAX_TOTAL_COST:
            print(f"==================================================")
            print(f"Cost threshold ({MAX_TOTAL_COST}) reached. Stopping execution.")
            print(f"Final accumulated cost: {accumulated_cost}")
            print(f"==================================================")
            break
            
        project_path = os.path.join(projects_dir, project_name)
        
        # Check if it's a directory
        if os.path.isdir(project_path):
            desc_file = os.path.join(project_path, 'desc.txt')
            
            # Read desc.txt if it exists
            if os.path.exists(desc_file):
                with open(desc_file, 'r', encoding='utf-8') as f:
                    desc_content = f.read()
                
                # title is the name of the subfolder, desc comes from desc.txt
                prompt = Prompt(title=project_name, desc=desc_content)
                
                print(f"==================================================")
                print(f"Running agent for project: {project_name}")
                print(f"==================================================")
                
                start_time = time.time()
                try:
                    # execute the run function from agent.py
                    cost = run(prompt=prompt)
                    end_time = time.time()
                    execution_time = end_time - start_time
                    accumulated_cost += cost
                    
                    # Log to CSV
                    with open(csv_file_path, mode='a', newline='') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writerow({
                            'project_name': project_name,
                            'execution_time_seconds': round(execution_time, 2),
                            'cost': round(cost, 4),
                            'accumulated_cost': round(accumulated_cost, 4)
                        })
                        
                    print(f"Finished project: {project_name}. Execution Time: {execution_time:.2f}s. Cost: {cost}. Accumulated Cost: {accumulated_cost}")
                except Exception as e:
                    print(f"Error running agent for {project_name}: {e}")
            else:
                print(f"Skipping {project_name}: desc.txt not found in project folder.")

if __name__ == "__main__":
    main()
