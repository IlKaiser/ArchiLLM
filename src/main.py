import streamlit as st
import asyncio
import json
import openai
import nest_asyncio
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex


import os
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)


from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.retrievers import QueryFusionRetriever

# Create your index
from llama_index.core import VectorStoreIndex
import qdrant_client

from archi import DalleWorkflow



# Apply nest_asyncio to allow running asyncio event loops within Streamlit's event loop
nest_asyncio.apply()



# --- Streamlit UI ---

st.set_page_config(page_title="Microservice Architecture Generator", layout="wide")
st.title("🏛️ Microservice Architecture Generator")
st.markdown("Based on the workflow from the `dalle.ipynb` notebook. This tool takes a project description and user stories to suggest a microservice architecture.")

# Pre-populate with example data from the notebook
S_EXAMPLE = """Not Far(m) From Home is a platform that allows a direct interaction between local farmers and consumers, with the main purpose of being “km 0”.
The Farmers will be able to post their fresh produce in the site, and the consumers to reserve the produce and select a day for the pickup at the Agricoltural Company."""

US_EXAMPLE = """
1) As a Client , I want to be able to Register in the site so that I can use the site
2) As a Client , I want to be able to login in the site so that I can use the site
3) As a Client , I want to be able to not put my Credentials in the site every time a reload the site, so that I can use the site
4) As a Client , I want to be able to logout, so that no one else use my account
5) As a Client , I want to be able to see my personal information
6) As a Client , I want to be able to Hot products, so that i can discover the product in the season
7) As a Client , I want to be able to See Agricultural company in my area, so that i can choose where to buy products
8) As a Client , I want to be able to See The products for each Agricultural company, so that I can buy From them
9) As a Client , I want to be able to Add to cart the products, so that i can buy them
10) As a Client, I want to be able to Remove products to the cart, so that i can decide what to buy
11) As a Client , I want to be able to see product in the cart, so that i can see want I am going to buy
12) As a Client , I want to be able to Complete an order, so that I can choose a date to go and pick up the products
13) As a Client , I want to be able to Open in google Maps the Location of the Agricultural company, so that i can find directions to it easly
14) As an Agricultural Company, I want to be able to Add products in inventory, so that I can show my clients the new produce
15) As an Agricultural Company, I want to be able to Remove products in inventory, so that My clients don't try to buy an item that I don't have anymore
16) As an Agricultural Company, I want to be able to Modify products in inventory, so that I can change price and quantities on the same item
17) As an Agricultural Company, I want to be able to Registrer in the site, so that i can be visible and start doing business in the site
18) As an Agricultural Company, I want to be able to Login, so that i can work on the site
19) As an Agricultural Company, I want to be able to ot put my Credentials in the site every time a reload the site, so that I can use the site easily
20) As an Agricultural Company, I want to be able to logout from the site
21) As an Agricultural Company, I want to be able to see my personal information
22) As the Administrator of the site, I want to be able to login in the site, so that i can work on it
23) As the Administrator of the site, I want to be able to not put my Credentials in the site every time a reload the site, so that I can use the site easily
24) As the Administrator of the site, I want to be able to logout from the site
25) As the Administrator of the site, I want to be able to delete malevolus user, so that the platform is reliable
"""


# --- Index & retriever loader ---
@st.cache_resource
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
        similarity_top_k=3,
        num_queries=4,
        mode="reciprocal_rerank",
        use_async=True,
        verbose=True,
    )
    return retriever


async def main():
    # Get OpenAI API Key
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")

    col1, col2 = st.columns(2)
    with col1:
        specs_input = st.text_area("📋 Project Description", value=S_EXAMPLE, height=250)
    with col2:
        user_stories_input = st.text_area("📝 User Stories", value=US_EXAMPLE, height=250)

    if st.button("🚀 Generate Architecture", use_container_width=True):
        if not api_key:
            st.error("Please enter your OpenAI API Key to proceed.")
        elif not specs_input or not user_stories_input:
            st.error("Please provide both a project description and user stories.")
        else:
            # Set the API key for OpenAI
            os.environ["OPENAI_API_KEY"] = api_key
            openai.api_key = os.environ["OPENAI_API_KEY"]


            with st.spinner("🧠 Running the architecture generation workflow... Please wait."):
                try:
                
                    # With nest_asyncio applied, we can use asyncio.run directly
                    retriever = get_retrievers()
                    wf = DalleWorkflow(timeout=None)
                    result_event = await wf.run(specs=specs_input, user_stories=user_stories_input, retriever=retriever)
                    
                    st.success("🎉 Workflow completed successfully!")
                    
                    st.subheader("Generated Architecture (JSON)")
                    
                    # Attempt to parse and display the JSON result
                    try:
                        # The result is now directly the JSON string from the last step
                        json_result = json.loads(result_event)
                        st.json(json_result)
                    except (json.JSONDecodeError, TypeError) as e:
                        st.error(f"Failed to parse the final result as JSON. Error: {e}")
                        st.text("Raw output:")
                        st.code(result_event[1], language='text')

                except Exception as e:
                    st.error(f"An error occurred during the workflow execution: {e}")
                    import traceback
                    st.code(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())

