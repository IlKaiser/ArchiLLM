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

def get_retrievers():
    # load or build the “sito” index
    # assume you have a persist_dir or vector_store prepared
    # e.g.:
    # index_sito = VectorStoreIndex.from_vector_store(my_vector_store)
    lock_file = os.path.join("/Users/marcocalamo/home/archi", ".lock")
    if os.path.exists(lock_file):
        os.remove(lock_file)

    os.makedirs("/Users/marcocalamo/home/archi", exist_ok=True)
    client = qdrant_client.AsyncQdrantClient(path="/Users/marcocalamo/home/archi")
    vector_store = QdrantVectorStore(aclient=client, collection_name="micro", use_async=True)
    index_sito = VectorStoreIndex.from_vector_store(vector_store)

    # load or build the “libro” index from disk
    persist_dir = "/Users/marcocalamo/Downloads/micro/persist"
    if os.path.exists(persist_dir):
        storage = StorageContext.from_defaults(persist_dir=persist_dir)
        index_libro = load_index_from_storage(storage)
    else:
        docs = SimpleDirectoryReader("/Users/marcocalamo/Downloads/micro/").load_data()
        index_libro = VectorStoreIndex.from_documents(docs)
        index_libro.storage_context.persist(persist_dir=persist_dir)

    retriever = QueryFusionRetriever(
        [
            index_sito.as_retriever(similarity_top_k=3),
            index_libro.as_retriever(similarity_top_k=3),
        ],
        similarity_top_k=5,
        num_queries=4,
        mode="reciprocal_rerank",
        use_async=True,
        verbose=True,
    )
    return retriever


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

async def process_folders(main_folder, output_excel_path):
    data = []
    retriever = get_retrievers()
    
    
    for subfolder in os.listdir(main_folder):
        subfolder_path = os.path.join(main_folder, subfolder)
        input_path = os.path.join(subfolder_path, "input.txt")

        if not os.path.isdir(subfolder_path) or not os.path.isfile(input_path):
            continue
        
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        system_description, user_stories = extract_sections(content)
        
        
        wf = DalleWorkflow(timeout=None)
        result_event = await wf.run(specs=system_description, user_stories=user_stories, retriever=retriever)
        output = json.loads(result_event)
        

        data.append({
            "Subfolder": subfolder,
            "System Description": system_description,
            "User Stories": user_stories,
            "Dalle Output": output
        })

    df = pd.DataFrame(data)
    df.to_excel(output_excel_path, index=False)

# Example usage:


def main():
    import asyncio
    asyncio.run(process_folders("/Users/marcocalamo/Downloads/docs/OPEN SOURCE", "results_open.xlsx"))

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Apply nest_asyncio to allow nested event loop
    main()