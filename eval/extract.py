import pandas as pd
import json
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def single_quote_to_double(str_in) -> str:
    """
    A function to parse a string and convert it into a valid JSON format.
    It replaces single quotes with double quotes
    """
    # Replace single quotes with double quotes except when they are inside double quotes.
    opend = False
    str_out = ""
    for c in str_in:
        if c != "'":
            if c == '"' and not opend:
                opend = True
            elif c == '"' and opend:
                opend = False
            str_out += c
        else:
            if opend:
                str_out += c
            else:
                str_out += '"'
    
  
    
    return str_out

# --- Configuration ---
input_excel_file = "results_open.xlsx"
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
        try:
            json_data = json.loads(row[json_column_name])
        except json.JSONDecodeError:
            json_data = json.loads(single_quote_to_double(row[json_column_name]))
            print(json_data["microservices"])

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
                print(f"Processed microservice in {subfolder}: {micro.get('name', 'N/A')}")
            print(grouped_microservices)
    except Exception as e:
        print(f"Error processing row {idx}: {e}")

print(f"Total subfolders processed: {len(grouped_microservices)}")
print(f"Sample subfolder keys: {list(grouped_microservices.keys())[:5]}")

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