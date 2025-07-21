import pandas as pd
import json
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# --- Configuration ---
input_excel_file = "/Users/marcocalamo/DALLE/results_open.xlsx"
json_column_name = "Dalle Output"  # Replace with the actual column name
sheet_name_column = "Subfolder"  # Column used to name the sheets
column_name = "microservices"  # Column containing the microservices data
blacklist = ["endpoints", "user_stories", "parameters"]  # Columns to be removed from the output
output_excel_file = f"NUOVO_OPEN_{column_name}.xlsx"

# --- Step 1: Read the Excel file ---
df = pd.read_excel(input_excel_file)

# --- Step 2: Group microservices by Subfolder ---
grouped_microservices = defaultdict(list)

for idx, row in df.iterrows():
    try:
        subfolder = str(row[sheet_name_column]).strip()
        json_data = json.loads(row[json_column_name])
        microservices = json_data.get(column_name, [])

        if isinstance(microservices, dict):
            microservices = [microservices]

        for micro in microservices:
            if isinstance(micro, dict):
                # Remove blacklisted keys
                for key in blacklist:
                    if key in micro:
                        del micro[key]
                # Flatten user_stories and parameters if present
                for key in ["user_stories", "parameters", "involved_microservices"]:
                    
                    
                    if key in micro:
                        micro[key] = ','.join(micro[key])
                    

                grouped_microservices[subfolder].append(micro)

    except Exception as e:
        print(f"Error processing row {idx}: {e}")

# --- Step 3: Write to Excel ---
wb = Workbook()
wb.remove(wb.active)  # Remove default sheet

for subfolder, micro_list in grouped_microservices.items():
    sheet_name = subfolder.replace(":", "_").replace("/", "_")[:31]

    micro_df = pd.json_normalize(micro_list, max_level=1)

    ws = wb.create_sheet(title=sheet_name)

    for r in dataframe_to_rows(micro_df, index=False, header=True):
        ws.append(r)

# --- Step 4: Save ---
wb.save(output_excel_file)
print(f"Created: {output_excel_file}")