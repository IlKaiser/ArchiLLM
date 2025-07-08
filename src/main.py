import streamlit as st
import asyncio
import json
import ast
import nest_asyncio
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event
)
import os
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)

from llama_index.llms.openai import OpenAI
from llama_index.core.schema import (
    NodeWithScore,
    TextNode,
)
from llama_index.core.response_synthesizers import (
    get_response_synthesizer,
    ResponseMode
)
from llama_index.core.prompts import RichPromptTemplate, PromptTemplate


from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.retrievers import QueryFusionRetriever

# Create your index
from llama_index.core import VectorStoreIndex
import qdrant_client



from typing import Any, List

# Apply nest_asyncio to allow running asyncio event loops within Streamlit's event loop
nest_asyncio.apply()

# --- Mock Objects and Data (for speed and simplicity) ---
# To make the app fast and avoid local file dependencies, we'll mock the retriever.
# In a real-world scenario, you would replace this with your actual index loading and retrieval logic.

class MockRetriever:
    """A mock retriever to simulate the behavior of the real one for speed."""
    def retrieve(self, query):
        st.info(f"🔍 Mock Retriever received query: '{query}'")
        # Creating a few dummy nodes to simulate the retrieval process.
        # The content of these nodes would normally come from your documents.
        mock_nodes = [
            NodeWithScore(node=TextNode(text="Context point 1: An API Gateway is a good pattern for managing requests."), score=0.9),
            NodeWithScore(node=TextNode(text="Context point 2: Use a Service Registry for dynamic service discovery."), score=0.88),
            NodeWithScore(node=TextNode(text="Context point 3: The Saga pattern is ideal for managing distributed transactions across services."), score=0.85),
            NodeWithScore(node=TextNode(text="Context point 4: CQRS is useful for separating read and write operations, improving performance."), score=0.82),
            NodeWithScore(node=TextNode(text="Context point 5: Event Sourcing can be used to capture all changes to an application state as a sequence of events."), score=0.80),
            NodeWithScore(node=TextNode(text="Context point 6: A Transactional Outbox ensures reliable messaging between services."), score=0.78),
        ]
        return mock_nodes

# --- Workflow Events ---

class RetrieverEvent(Event):
    """Result of running retrieval"""
    nodes: list[NodeWithScore]

class CreateCitationsEvent(Event):
    """Add citations to the nodes."""
    nodes: list[NodeWithScore]

class MicroservicesExtractedEvent(Event):
    """Get list of microservices from specs and user stories"""
    microservices_list: list[str]

class ContextRetrievedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    context: Any

# --- Prompts ---

EXTRACT_MICROSERVICES_TEXT = """
You will be asked to extract a list of microservices from specifications and user stories.
Report the list in a format like this:
['Microservice1',  'Mircoservice2', ...]

The context is:
Specifications:
--------------------
{{specs}}
--------------------
User Stories:
--------------------
{{user_stories}}
--------------------

The microservice list is:
"""

FIND_CONTEXT_TEXT = """
What are the best microservices patterns to use for this microservices list {{microservices_list}} given these user stories: {{user_stories}} and descriptions:{{specs}}?
"""

USE_CONTEXT_TEXT = """
Given a microservice list, text specifications and user stories of a software,
use context to find the best implementation pattern for each microservice.
Include an explaination on what source made you make a certain choice.
Add also what endpoints are implemented if needed for each microservice, with a corresponding description of inputs and outputs.
Add for every micorservice what user stories it implements, indicating it with their corresponding number, and only the number. All user stories must be implemented.
Find also which microservices require a dataset and provide a brief description of it by saying what user stories influenced your choices.
Output data in a json format like this:

{
    microservices: [
        { 
            name: "name1",
            endpoints: [],
            user_stories: ["story1"]
        }, 
        {
            name: "name2",
            endpoints: [
                { 
                    name: "/login",
                    description: "takes user email and password as inputs and outputs the login result"
                }, 
                {
                    name:"/register"
                    description: "takes user email and password as inputs and outputs the registration result"
                }
            ]
            user_stories: ["story2", "story3"]
        } 
    ],
    patterns: [
            {
                group_name : "meaningful name",
                implementation_pattern: "saga",
                involved_microservices: ["name1", "name2"],
                explaination: "xyz"
                
            },
            {
                group_name : "meaningful name",
                implementation_pattern: "api gateway",
                involved_microservices: ["name3"],
                explaination: "vwq"
            }
    ],
    datasets: [
            {
                dataset_name: "meaningful name",
                associtated_microservice: "name3",
                description: "desc"
            },
    ]

}



The context is:

Retrieved Context
--------------------
{{context}}
--------------------

Microservice List
--------------------
{{microservice_list}}
--------------------

Specifications:
--------------------
{{specs}}
--------------------

User Stories:
--------------------
{{user_stories}}
--------------------

The output json is:
"""

CITATION_QA_TEMPLATE = PromptTemplate(
    "Please provide an answer based solely on the provided sources. "
    "When referencing information from a source, "
    "cite the appropriate User Story(ies) using their corresponding numbers. "
    "Every answer should include at least one source citation. "
    "Only cite a source when you are explicitly referencing it. "
    "If none of the sources are helpful, you should indicate that. "
    "\n------\n"
    "{context_str}"
    "\n------\n"
    "Query: {query_str}\n"
    "Answer: "
)

# --- Workflow Definitions ---

class CitationQueryEngineWorkflow(Workflow):
    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrieverEvent | None:
        query = ev.get("query")
        if not query:
            return None
        await ctx.set("query", query)

        retriever = ev.retriever
        if retriever is None:
            print("Retriever is empty!")
            return None

        nodes = retriever.retrieve(query)
        st.write(f"✅ Retrieved {len(nodes)} nodes for context.")
        return RetrieverEvent(nodes=nodes)

    @step
    async def create_citation_nodes(self, ev: RetrieverEvent) -> CreateCitationsEvent:
        return CreateCitationsEvent(nodes=ev.nodes)

    @step
    async def synthesize(self, ctx: Context, ev: CreateCitationsEvent) -> StopEvent:
        llm = OpenAI(model="gpt-4o-mini")
        query = await ctx.get("query", default=None)
        synthesizer = get_response_synthesizer(
            llm=llm,
            text_qa_template=CITATION_QA_TEMPLATE,
            response_mode=ResponseMode.TREE_SUMMARIZE,
            use_async=True,
        )
        response = await synthesizer.asynthesize(query, nodes=ev.nodes)
        return StopEvent(result=response)


class DalleWorkflow(Workflow):
    @step
    async def extract_microservices(self, ctx: Context, ev: StartEvent) -> MicroservicesExtractedEvent:
        llm = OpenAI(model="gpt-4o-mini")
        await ctx.set("llm", llm)
        await ctx.set("specs", ev.specs)
        await ctx.set("user_stories", ev.user_stories)
        await ctx.set("retriever", ev.retriever)

        extract_template = RichPromptTemplate(EXTRACT_MICROSERVICES_TEXT)
        extract_query = extract_template.format(specs=ev.specs, user_stories=ev.user_stories)

        resp = llm.complete(extract_query).text
        try:
            resp_list = ast.literal_eval(resp)
        except (ValueError, SyntaxError):
            st.error("Could not parse the list of microservices from the LLM response.")
            resp_list = []
            
        st.write("✅ Extracted Microservices List.")
        return MicroservicesExtractedEvent(microservices_list=resp_list)

    @step
    async def retrieve_context(self, ctx: Context, ev: MicroservicesExtractedEvent) -> ContextRetrievedEvent:
        print("Retrieving context for microservices:", ev.microservices_list)
        specs = await ctx.get("specs")
        user_stories = await ctx.get("user_stories")
        retriever = await ctx.get("retriever")
        llm = await ctx.get("llm")

        find_context_template = RichPromptTemplate(FIND_CONTEXT_TEXT)
        context_query = find_context_template.format(
            specs=specs,
            user_stories=user_stories,
            microservices_list=ev.microservices_list
        )

        citation_workflow = CitationQueryEngineWorkflow(timeout=None)
        context_response = await citation_workflow.run(query=context_query, retriever=retriever)

        print("Context response:", context_response)
        
        st.write("✅ Retrieved Context from Retriever.")

        use_context_template = RichPromptTemplate(USE_CONTEXT_TEXT)
        final_query = use_context_template.format(
            specs=specs,
            context=str(context_response),
            user_stories=user_stories,
            microservice_list=ev.microservices_list
        )
        
        resp = llm.complete(final_query).text

        print("Final query response:", resp)
        st.write("✅ Generated Final Architecture.")
        return ContextRetrievedEvent(context=resp)

    @step
    async def format_output(self, ctx: Context, ev: ContextRetrievedEvent) -> StopEvent:
        return StopEvent(result=ev.context)


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
            import os
            os.environ["OPENAI_API_KEY"] = api_key

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
                        json_result = json.loads(result_event[7:-3])
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

