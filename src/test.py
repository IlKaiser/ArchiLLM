from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event
)

from llama_index.llms.mistralai import MistralAI
from llama_index.llms.openai import OpenAI
from llama_index.llms.anthropic import Anthropic

from llama_index.core.schema import (
    NodeWithScore,
)
from llama_index.core.response_synthesizers import (
    get_response_synthesizer,
    ResponseMode
)


from llama_index.core.prompts import RichPromptTemplate, PromptTemplate
from llama_index.core.program import LLMTextCompletionProgram

import streamlit as st
import json

from typing import Any

from output import DalleOutput, DalleOutputCode
from utils import single_quote_to_double, single_quote_to_double_with_content, to_dict
from prompts import (
    EXTRACT_MICROSERVICES_TEXT,
    FIND_CONTEXT_TEXT,
    USE_CONTEXT_TEXT,
    GENERATE_CODE_TEXT
)   

# add near the top with your other imports
import io
import zipfile
import base64
import posixpath

# --- Workflow Events ---

class RetrieverEvent(Event):
    """Result of running retrieval"""
    nodes: list[NodeWithScore]

class CreateCitationsEvent(Event):
    """Add citations to the nodes."""
    nodes: list[NodeWithScore]

class MicroservicesExtractedEvent(Event):
    """Get list of microservices from specs and user stories"""
    microservices_list: str

class ContextRetrievedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    context: Any

class CodeGeneratedEvent(Event):
    """Get ready to generate final output with context and ms. list"""
    code: Any


CITATION_QA_TEMPLATE = PromptTemplate(
    "Please provide an answer based solely on the provided sources. "
    "When referencing information from a source, "
    "cite the appropriate User Story(ies) using their corresponding numbers. "
    "Every answer should include at least one source citation. "
    "Only cite a source when you are explicitly referencing it. "
    "Only these patterns are allowed: Communication style patterns (shared database, database per service) and Data style patterns (api composition, cqrs, saga, aggregate, event sourcing, domain event) and DO NOT USE OTHER PATTERNS."
    "If none of the sources are helpful, you should indicate that. "
    "\n------\n"
    "{context_str}"
    "\n------\n"
    "Query: {query_str}\n"
    "Answer: "
)
# --- Workflow Definitions ---
import os 
from dotenv import load_dotenv
assert load_dotenv()

class CitationQueryEngineWorkflow(Workflow):
    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrieverEvent:
        await ctx.store.set("model", ev.model)
        query = ev.get("query")
        if not query:
            return None
        await ctx.store.set("query", query)

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
        model = await ctx.store.get("model")
        if model == "mistral":
            llm = MistralAI(model="mistral-large-2411", temperature=0, timeout=9999.0, max_tokens=9000)
        elif model in ("claude", "anthropic"):
            llm = Anthropic(model="claude-sonnet-4-5", temperature=1.0, max_tokens=64000, timeout=9999.0)
        else:
            llm = OpenAI(model="gpt-4.1", temperature=0, timeout=9999.0)

        query = await ctx.store.get("query", default=None)
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
        await ctx.store.set("specs", ev.specs)
        await ctx.store.set("user_stories", ev.user_stories)
        await ctx.store.set("retriever", ev.retriever)
        await ctx.store.set("model", ev.model)

        model = await ctx.store.get("model")
        if model == "mistral":
            llm = MistralAI(model="mistral-large-2411", temperature=0, timeout=9999.0, max_tokens=9000)
        elif model in ("claude", "anthropic"):
            llm = Anthropic(model="claude-sonnet-4-5", temperature=1.0, max_tokens=64000, timeout=9999.0)
        else:
            llm = OpenAI(model="gpt-4.1", temperature=0, timeout=9999.0)
        await ctx.store.set("llm", llm)

        print("The model being used is:", model)
        # set env model MODEL
        os.environ["MODEL"] = model

        extract_template = RichPromptTemplate(EXTRACT_MICROSERVICES_TEXT)
        extract_query = extract_template.format(specs=ev.specs, user_stories=ev.user_stories)

        resp = llm.complete(extract_query).text
        try:
            resp_list = resp
        except (ValueError, SyntaxError):
            st.error("Could not parse the list of microservices from the LLM response.")
            resp_list = ""
            
        st.write("✅ Extracted Microservices List.")
        return MicroservicesExtractedEvent(microservices_list=resp_list)

    @step
    async def retrieve_context(self, ctx: Context, ev: MicroservicesExtractedEvent) -> StopEvent:
        print("Retrieving context for microservices:", ev.microservices_list)
        specs = await ctx.store.get("specs")
        user_stories = await ctx.store.get("user_stories")
        retriever = await ctx.store.get("retriever")

        model = await ctx.store.get("model")
        if model == "mistral":
            llm = MistralAI(model="mistral-large-2411", temperature=0, timeout=9999.0, max_tokens=9000)
        elif model in ("claude", "anthropic"):
            llm = Anthropic(model="claude-sonnet-4-5", temperature=1.0, max_tokens=64000, timeout=9999.0)
        else:
            llm = OpenAI(model="gpt-4.1", reasoning_effort="low", temperature=0, timeout=9999.0)
        
        #sllm = llm.as_structured_llm(output_cls=DalleOutput)

        find_context_template = RichPromptTemplate(FIND_CONTEXT_TEXT)
        
        context_query = find_context_template.format(
            specs=specs,
            user_stories=user_stories,
            microservices_list=ev.microservices_list
        )

        citation_workflow = CitationQueryEngineWorkflow(timeout=None)
        context_response = await citation_workflow.run(model=model, query=context_query, retriever=retriever)
        print("Context response:", context_response)
        
        st.write("✅ Retrieved Context from Retriever.")

        #use_context_template = RichPromptTemplate(USE_CONTEXT_TEXT)
    
        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutput,
            prompt_template_str=USE_CONTEXT_TEXT,
            llm=llm,
            verbose=True,
        )
        
        output = program(
            specs=specs,
            context=str(context_response),
            user_stories=user_stories,
            microservice_list=ev.microservices_list,
        )

        print("Output from LLM:", to_dict(output))

        await ctx.store.set("archi_json", to_dict(output))

        #resp = single_quote_to_double(str(sllm.complete(final_query).raw.dict()))
        #print("Final response:", resp)
        
        st.write("✅ Generated Final Architecture.")
        st.json(single_quote_to_double(str(to_dict(output))))

        return StopEvent(result=to_dict(output))

