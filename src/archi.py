from llama_index.core.workflow import (
    Context,
    Workflow,
    StartEvent,
    StopEvent,
    step,
    Event
)

from llama_index.llms.openai import OpenAI
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

from output import DalleOutput
from utils import single_quote_to_double, to_dict
from prompts import (
    EXTRACT_MICROSERVICES_TEXT,
    FIND_CONTEXT_TEXT,
    USE_CONTEXT_TEXT,
)   



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
        llm = OpenAI(model="gpt-4.1")
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
        llm = OpenAI(model="gpt-4.1")
        await ctx.set("llm", llm)
        await ctx.set("specs", ev.specs)
        await ctx.set("user_stories", ev.user_stories)
        await ctx.set("retriever", ev.retriever)

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
    async def retrieve_context(self, ctx: Context, ev: MicroservicesExtractedEvent) -> ContextRetrievedEvent:
        print("Retrieving context for microservices:", ev.microservices_list)
        specs = await ctx.get("specs")
        user_stories = await ctx.get("user_stories")
        retriever = await ctx.get("retriever")
        llm = await ctx.get("llm")
        #sllm = llm.as_structured_llm(output_cls=DalleOutput)

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

        #resp = single_quote_to_double(str(sllm.complete(final_query).raw.dict()))
        #print("Final response:", resp)
        
        st.write("✅ Generated Final Architecture.")
        return ContextRetrievedEvent(context=single_quote_to_double(str(to_dict(output))))

    @step
    async def format_output(self, ctx: Context, ev: ContextRetrievedEvent) -> StopEvent:
        """Format the final output into a structured JSON format."""
        
        return StopEvent(result=json.dumps(ev.context, indent=2, ensure_ascii=False))

