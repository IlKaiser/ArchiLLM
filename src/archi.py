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

from llama_index.llms.anthropic import Anthropic
from llama_index.llms.groq import Groq
from llama_index.llms.gemini import Gemini


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

from dotenv import load_dotenv
assert load_dotenv()

class CitationQueryEngineWorkflow(Workflow):
    @step
    async def retrieve(self, ctx: Context, ev: StartEvent) -> RetrieverEvent:
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
        llm = OpenAI(model="gpt-4.1")
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
        llm = OpenAI(model="gpt-4.1") #, reasoning_effort="low", temperature=0, timeout=9999.0)
        await ctx.store.set("llm", llm)
        await ctx.store.set("specs", ev.specs)
        await ctx.store.set("user_stories", ev.user_stories)
        await ctx.store.set("retriever", ev.retriever)

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
        specs = await ctx.store.get("specs")
        user_stories = await ctx.store.get("user_stories")
        retriever = await ctx.store.get("retriever")
        
        
        #llm = await ctx.store.get("llm")
        llm = OpenAI(model="gpt-5-mini" , reasoning_effort="minimal", temperature=0, timeout=9999.0)
        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)

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
        st.json(single_quote_to_double(str(to_dict(output))))
        return ContextRetrievedEvent(context=single_quote_to_double(str(to_dict(output))))
    @step
    async def generate_code(self, ctx: Context, ev: ContextRetrievedEvent) -> CodeGeneratedEvent:
        """Generate code snippets for each microservice based on the architecture."""
        
        #llm = await ctx.store.get("llm")

        llm = OpenAI(model="gpt-5-mini" , reasoning_effort="medium", temperature=0, timeout=9999.0)
        #llm = Anthropic(model="claude-sonnet-4-5", temperature=0, max_tokens=19_000, timeout=9999.0)
        #llm = Groq(model="openai/gpt-oss-120b", temperature=0, max_tokens=19_000, timeout=9999.0)

        #llm = Gemini(model="gemini-2.5-flash", temperature=0, timeout=9999.0)


        program = LLMTextCompletionProgram.from_defaults(
            output_cls=DalleOutputCode,
            prompt_template_str=GENERATE_CODE_TEXT,
            llm=llm,
            verbose=True,
        )

        
        output = program(
            input_json=ev.context,
        )
        print("Code Output from LLM:", to_dict(output))
        st.write("✅  Generated code snippets for microservices.")
        return CodeGeneratedEvent(code=single_quote_to_double_with_content(str(to_dict(output))))
    
    @step
    async def package_zip(self, ctx: Context, ev: CodeGeneratedEvent) -> StopEvent:
        """
        Convert the generated microservices JSON into a ZIP archive.
        The JSON is expected to follow the schema:
        { "folders": [ { "name": str, "folders": [...], "files": [{"name": str, "content": str}] } ],
          "files":   [ { "name": str (can include nested paths like 'a/b/c.txt'), "content": str } ] }
        Returns: StopEvent(result={"filename": "...zip", "zip_base64": "<base64-zip>"})
        """
        # Parse the JSON produced by the previous step
        try:
            structure = ev.code
            print("Generated code structure:", structure)
            with open("debug_generated_code.txt", "w") as f:
                f.write(str(structure))
            if isinstance(structure, str):
                structure = json.loads(structure)
        except Exception as e:
            st.error(f"❌ Could not parse generated code JSON: {e}")
            return StopEvent(result={"error": f"Invalid JSON from CodeGeneratedEvent: {e}"})

        # Helpers to write the file-tree directly into a ZIP (no temp files needed)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

            def _write_files(files: list | None, base: str = ""):
                if not files:
                    return
                for f in files:
                    name = (f or {}).get("name", "")
                    content = (f or {}).get("content", "")
                    if not name:
                        continue
                    # Support names that already include nested paths (e.g., "src/main/.../User.java")
                    arcpath = posixpath.join(base, name).lstrip("/")
                    # Ensure directory placeholders for nicer unzip UX (optional)
                    dirpart = posixpath.dirname(arcpath)
                    if dirpart and not dirpart.endswith("/"):
                        zf.writestr(dirpart + "/", "")
                    zf.writestr(arcpath, content or "")

            def _write_folders(folders: list | None, base: str = ""):
                if not folders:
                    return
                for folder in folders:
                    if not folder:
                        continue
                    folder_name = folder.get("name", "")
                    folder_path = posixpath.join(base, folder_name).strip("/")
                    # Add an explicit directory entry
                    if folder_path:
                        zf.writestr(folder_path + "/", "")
                    # Write files in this folder
                    _write_files(folder.get("files", []), folder_path)
                    # Recurse into subfolders
                    _write_folders(folder.get("folders", []), folder_path)

            # Top-level files (may include full nested paths)
            _write_files(structure.get("files", []), "")
            # Foldered structure
            _write_folders(structure.get("folders", []), "")

        buf.seek(0)
        zip_b64 = base64.b64encode(buf.read()).decode("ascii")
        payload = {
            "filename": "microservices_project.zip",
            "zip_base64": zip_b64,
        }
        st.write("✅ Packaged microservices code as a ZIP.")
        return StopEvent(result=payload)

