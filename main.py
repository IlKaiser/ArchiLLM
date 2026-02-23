import _frozen_importlib
import os

from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.terminal import TerminalTool
from openhands.tools.apply_patch import ApplyPatchTool

from openhands.sdk.tool import register_tool
from openhands.tools.delegate import (
    DelegateTool,
    DelegationVisualizer,
    register_agent,
)

from openhands.tools.preset.default import get_default_tools

from prompt import BACKEND_PROMPT, BACKEND_PROMPT_PYTHON, FRONTEND_PROMPT, title

from dotenv import load_dotenv
load_dotenv()


create_backend = True
create_frontend = True
use_spring_boot = False

llm = LLM(
    model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", None),
    temperature=0.0,
    top_p=None,
    usage_id="agent"
)


tools = [
    Tool(name=FileEditorTool.name),
    Tool(name=TaskTrackerTool.name),
    Tool(name=TerminalTool.name),
    #Tool(name=ApplyPatchTool.name),
    #Tool(name=DelegateTool.name),
]

agent = Agent(
    llm=llm,
    tools=tools,
    visualize=DelegationVisualizer(name="Delegator Backend"),
)

cwd = os.getcwd()

conversation = Conversation(agent=agent, workspace=cwd)

conversation.send_message(f"Create a working directory for the project if not already existing, call it {title}.")
conversation.run()

backend_cost = 0
frontend_cost = 0

if create_backend:
    
    agent = Agent(
        llm=llm,
        tools=tools,
        visualize=DelegationVisualizer(name="Delegator Backend"),
    )


    conversation = Conversation(agent=agent, workspace=cwd)

    if use_spring_boot:
            conversation.send_message(BACKEND_PROMPT)
    else:
        conversation.send_message(BACKEND_PROMPT_PYTHON)
    conversation.run()
    print("All done!")

    backend_cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
    print(f"BACKEND COST (simple delegation): {backend_cost}")

if create_frontend:
    agent = Agent(
        llm=llm,
        tools=tools,
        visualize=DelegationVisualizer(name="Delegator Frontend"),
    )

    cwd = os.getcwd()
    conversation = Conversation(agent=agent, workspace=cwd)

    conversation.send_message(FRONTEND_PROMPT)
    conversation.run()
    print("All done!")

    frontend_cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
    print(f"FRONTEND COST (simple delegation): {frontend_cost}")


final_cost = backend_cost + frontend_cost
print(f"TOTAL COST (simple delegation): {final_cost}")