import os
import json
import pandas as pd


is_open_dataset = True  # Set to True for open dataset, False for closed dataset


from functools import reduce

def avg_stories_per_service(gen):
    stories_per_service =  [len(dx['user_stories']) for dx in gen["microservices"]]
    return reduce(lambda a,b: a+b, stories_per_service)/len(stories_per_service), len(stories_per_service)

def compute_ussc(ref, gen):
    set_ref = set([ddx for dx in ref for ddx in dx['user_stories']])
    set_gen = set([int(ddx) for dx in json.loads(gen[1])["microservices"] for ddx in dx['user_stories']])
    prec = len(set_ref.intersection(set_gen)) / len(set_ref)
    return prec, len(set_gen), len(set_ref)

def compute_uscc_open(gen,txt):
    set_gen = set([int(ddx) for dx in gen["microservices"] for ddx in dx['user_stories']])
    with open(txt, 'r', encoding='utf-8-sig') as f:
        file_content = f.read()
        # split at user stories
        user_stories_section = file_content.split("# USER STORIES:")[1].strip()
        # count number of user stories as lines
        num_user_stories = len(user_stories_section.splitlines())

    prec = len(set_gen) / num_user_stories if num_user_stories > 0 else 0
    return prec, len(set_gen), num_user_stories

def main(excel_path, dataset_path, output_excel_path):
    # Read Excel file
    df = pd.read_excel(excel_path)
    ussc_scores = []
    sps_scores = []
    
    for idx, row in df.iterrows():
        folder_name = row['Subfolder']  # Adjust if the column is named differently
        dalle_output_json = row['Dalle Output']
        # Dalle Output is expected to be a JSON string or a list, adapt as needed
        if isinstance(dalle_output_json, str):
            # If the string is a list of json strings, take the first or parse as required
            dalle_output = json.loads(dalle_output_json)
        else:
            dalle_output = dalle_output_json
        # Ensure format: gen needs to be a list/tuple where gen[1] is a json string with "microservices"
        if isinstance(dalle_output, (list, tuple)):
            gen = dalle_output
        else:
            gen = [None, dalle_output_json]

        
        if is_open_dataset:
            score = compute_uscc_open(dalle_output, os.path.join(dataset_path, folder_name, 'input.txt'))
            

        else:
            metrics_path = os.path.join(dataset_path, folder_name, 'DataMetrics.json')
            
            
            try:
                # Load Data Metrics.json
                with open(metrics_path, 'r', encoding='utf-8-sig') as f:
                    ref_json = json.load(f)
                
                
                    
                # Compute USSC for the open dataset
                score = compute_ussc(ref_json, gen)
            except Exception as e:
                print(f'Error processing row {idx} ({folder_name}): {e}')
                score = None
        sps_score = avg_stories_per_service(dalle_output)

        ussc_scores.append(score)
        sps_scores.append(sps_score)
    
    df['USSC'] = [score[0] if score else None for score in ussc_scores]
    df['Generated User Stories Count'] = [score[1] if score else None for score in ussc_scores]
    df['Reference User Stories Count'] = [score[2] if score else None for score in ussc_scores]
    df['Average Stories per Service'] = [sps[0] if sps else None for sps in sps_scores]
    df['Total Services'] = [sps[1] if sps else None for sps in sps_scores]
    df.to_excel(output_excel_path, index=False)
    print(f"Results saved to {output_excel_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compute USSC and save results to Excel.")
    parser.add_argument("--excel", required=True, help="Path to the input Excel file.")
    parser.add_argument("--dataset", required=True, help="Path to the dataset directory.")
    parser.add_argument("--output", default="results_with_ussc.xlsx", help="Path for the output Excel file.")
    args = parser.parse_args()
    main(args.excel, args.dataset, args.output)
