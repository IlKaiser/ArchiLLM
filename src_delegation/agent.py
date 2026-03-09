import _frozen_importlib
import os

from openhands.sdk import (
    LLM,
    Agent,
    Conversation,
    Event,
    ImageContent,
    LLMConvertibleEvent,
    Message,
    Tool,
    TextContent,
    get_logger,
)
from openhands.sdk.llm.router import MultimodalRouter
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

from openhands.sdk.context.condenser import LLMSummarizingCondenser                                                              
                                                                                    
from openhands.tools.preset.default import get_default_tools

from src.prompt import Prompt

from dotenv import load_dotenv
load_dotenv()


def run(prompt: Prompt, create_backend: bool = True, create_frontend: bool = True, create_test: bool = True, use_spring_boot: bool = True) -> float:
    llm = LLM(
        model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
        condenser=LLMSummarizingCondenser(                                                                                           
            llm=LLM(model="anthropic/claude-sonnet-4-5-20250929", api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL", None)),                                                            
            max_size=20,  
            keep_first=4   
        ),                                      
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", None),
        temperature=0.0,
        top_p=None,
        usage_id="agent"
    )


    secondary_llm = LLM(
        usage_id="agent-secondary",
        model="openhands/qwen3-coder-480b",
        base_url=os.getenv("LLM_BASE_URL", None),
        api_key=os.getenv("OPENHANDS_API_KEY"),
        native_tool_calling=False,
        max_message_chars=50000,
        condenser=LLMSummarizingCondenser(
            llm=LLM(
                model="openhands/qwen3-coder-480b",
                base_url=os.getenv("LLM_BASE_URL", None), 
                api_key=os.getenv("OPENHANDS_API_KEY"),
                native_tool_calling=False
            ),
            max_size=20,
            keep_first=4
        )
    )
    
    def create_worker_agent(llm: LLM) -> Agent:
        worker_tools = [
            Tool(name=FileEditorTool.name),
            Tool(name=TerminalTool.name),
        ]
        # Ignore the passed-in LLM and use the cheaper secondary_llm explicitly
        return Agent(
            llm=secondary_llm,
            tools=worker_tools,
        )

    register_agent(
        name="worker",
        factory_func=create_worker_agent,
        description="A capable worker agent that is extremely good at running terminal commands, navigating the file system, editing files, and writing code logic. It does not have access to delegation tools.",
    )

    manager_tools = [
        Tool(name=DelegateTool.name, params={"max_children": 10}),
        Tool(name=TaskTrackerTool.name),
    ]

    from openhands.sdk.context.agent_context import AgentContext
    from openhands.sdk.context.skills.skill import Skill
    
    manager_context = AgentContext(
        skills=[
            Skill(
                name="delegator",
                content=(
                    "You are a Manager Agent. You DO NOT have tools to edit or list files. "
                    "When you need to create, modify, or view files, you MUST use the `delegate` tool "
                    "to spawn a `worker` agent. You should pass the generated code and explicit file operations "
                    "to the worker, and wait for its completion.\n"
                    "CRITICAL: If you have multiple independent tasks (e.g., generating multiple independent files in different folders, or exploring multiple structures), you MUST leverage parallelism. "
                    "The `delegate` tool supports spawning MULTIPLE agents at once by assigning them unique names. "
                    "For example, you can write `{\"worker_1\": \"Task 1\", \"worker_2\": \"Task 2\"}` in the tasks dictionary configuration. "
                    "Use this parallelism to run many workers simultaneously and save time!"
                ),
            )
        ]
    )

    agent = Agent(
        llm=llm,
        tools=manager_tools,
        agent_context=manager_context,
        visualize=DelegationVisualizer(name="Delegator Backend"),
    )

    cwd = os.getcwd()

    conversation = Conversation(agent=agent, workspace=cwd)

    conversation.send_message(f"Create a working directory for the project if not already existing, call it {prompt.title}.")
    conversation.run()

    backend_cost = 0.0
    frontend_cost = 0.0
    test_cost = 0.0

    if create_backend:
        
        agent = Agent(
            llm=llm,
            tools=manager_tools,
            agent_context=manager_context,
            #visualize=DelegationVisualizer(name="Delegator Backend"),
        )

        conversation = Conversation(agent=agent, workspace=cwd)

        if use_spring_boot:
            conversation.send_message(prompt.get_backend_prompt())
        else:
            conversation.send_message(prompt.get_backend_prompt_python())
        conversation.run()
        print("All done!")

        backend_cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
        print(f"BACKEND COST (simple delegation): {backend_cost}")

    if create_frontend:
        agent = Agent(
            llm=llm,
            tools=manager_tools,
            agent_context=manager_context,
            visualize=DelegationVisualizer(name="Delegator Frontend"),
        )

        cwd = os.getcwd()
        conversation = Conversation(agent=agent, workspace=cwd)

        conversation.send_message(prompt.get_frontend_prompt())
        conversation.run()
        print("All done!")

        frontend_cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
        print(f"FRONTEND COST (simple delegation): {frontend_cost}")    

    if create_test:
        agent = Agent(
            llm=llm,
            tools=manager_tools,
            agent_context=manager_context,
            visualize=DelegationVisualizer(name="Delegator Test"),
        )

        cwd = os.getcwd()
        conversation = Conversation(agent=agent, workspace=cwd)

        conversation.send_message(prompt.get_test_prompt())
        conversation.run()
        print("All done!")

        test_cost = conversation.conversation_stats.get_combined_metrics().accumulated_cost
        print(f"TEST COST (simple delegation): {test_cost}")

    final_cost = test_cost
    print(f"TOTAL COST (simple delegation): {final_cost}")
    return final_cost


if __name__ == "__main__":
    from src.prompt import prompt as default_prompt
    run(prompt=default_prompt)