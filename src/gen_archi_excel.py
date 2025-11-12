import os
import json
import pandas as pd
from archi import DalleWorkflow  # Assumes dalleworkflow is defined in main.py

from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)

from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.retrievers import QueryFusionRetriever
import qdrant_client

# load dot env
from dotenv import load_dotenv
load_dotenv()


def extract_sections(input_text):
    system_desc = ""
    user_stories = ""
    
    lines = input_text.splitlines()
    sys_start = usr_start = None
    
    for i, line in enumerate(lines):
        if line.strip() == "# SYSTEM DESCRIPTION:":
            sys_start = i + 1
        elif line.strip() == "# USER STORIES:":
            usr_start = i + 1

    if sys_start is not None and usr_start is not None:
        system_desc = "\n".join(lines[sys_start:usr_start-1]).strip()
        user_stories = "\n".join(lines[usr_start:]).strip()
    
    return system_desc, user_stories

async def process_folders(main_folder, output_excel_path, results_path="results_claude"):
    data = []
    
    
    
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        input_path = os.path.join(subfolder_path, "input.txt")

        if not os.path.isdir(subfolder_path) or not os.path.isfile(input_path):
            continue
        
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        system_description, user_stories = extract_sections(content)
        
        
        # Open results from a folder
        with open(os.path.join(results_path, f"{subfolder}.json"), "r", encoding="utf-8") as f:
            result_event = f.read()

        output = json.loads(result_event)
        

        data.append({
            "Subfolder": subfolder,
            "System Description": system_description,
            "User Stories": user_stories,
            "Dalle Output": output["output"]
        })

    df = pd.DataFrame(data)
    df.to_excel(output_excel_path, index=False)

# Example usage:


def main():
    import asyncio
    asyncio.run(process_folders(
    "dataset/open_source_projects", "results_open.xlsx", results_path="results_claude"))

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Apply nest_asyncio to allow nested event loop
    main()