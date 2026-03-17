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
    DelegationVisualizer
)

from openhands.sdk.subagent import register_agent

from openhands.sdk.context.condenser import LLMSummarizingCondenser                                                              
                                                                                    
from openhands.tools.preset.default import get_default_tools

from src.prompt import Prompt
from src.effort_router import EffortRouter

from dotenv import load_dotenv
load_dotenv()


def run(prompt: Prompt, create_backend: bool = True, create_frontend: bool = True, create_test: bool = True, use_spring_boot: bool = True, use_multi_agent: bool = False) -> float:
    llm = LLM(
        model=os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
        condenser=LLMSummarizingCondenser(                                                                                           
            llm=LLM(model="anthropic/claude-sonnet-4-5-20250929", api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL", None)),                                                            
            max_size=50,  
            keep_first=20   
        ),                                      
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", None),
        temperature=1.0,
        top_p=0.95,
        
        usage_id="agent"
    )


    secondary_llm = LLM(
        usage_id="agent-secondary",
        model=os.getenv("SECONDARY_LLM_MODEL", "openhands/devstral-medium-2507"),
        base_url=os.getenv("LLM_BASE_URL", None),
        api_key=os.getenv("SECONDARY_LLM_API_KEY"),
        condenser=LLMSummarizingCondenser(
            llm=LLM(
                model=os.getenv("SECONDARY_LLM_MODEL"),
                base_url=os.getenv("LLM_BASE_URL", None), 
                api_key=os.getenv("SECONDARY_LLM_API_KEY"),
                top_p=0.95,
                native_tool_calling=False
            ),
            max_size=50,
            keep_first=20
        ),
        top_p=0.95,
        native_tool_calling=False,
    )

    if use_multi_agent:
        llm = EffortRouter(
            usage_id="effort-router",
            llms_for_routing={"primary": llm, "secondary": secondary_llm},
        )


    tools = [
        Tool(name=FileEditorTool.name),
        Tool(name=TaskTrackerTool.name),
        Tool(name=TerminalTool.name),
        Tool(name=ApplyPatchTool.name),
        Tool(name=DelegateTool.name)
    ]
       

    agent = Agent(
        llm=llm,
        tools=tools,
        visualize=DelegationVisualizer(name="Delegator Backend"),
    )

    cwd = os.getcwd()

    backend_cost = 0.0
    frontend_cost = 0.0
    test_cost = 0.0

    if create_backend:
        
        agent = Agent(
            llm=llm,
            tools=tools,
            visualize=DelegationVisualizer(name="Delegator Backend"),
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
            tools=tools,
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

        llm = LLM(
            model=os.getenv("TEST_LLM_MODEL", "anthropic/claude-sonnet-4-5-20250929"),
            condenser=LLMSummarizingCondenser(                                                                                           
                llm=LLM(model="anthropic/claude-sonnet-4-5-20250929", api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL", None)),                                                            
                max_size=50,  
                keep_first=20   
            ),                                      
            api_key=os.getenv("TEST_LLM_API_KEY"),
            base_url=os.getenv("TEST_LLM_BASE_URL", None),
            temperature=1.0,
            top_p=0.95,
            
            usage_id="agent"
        )

        tools = [
            Tool(name=FileEditorTool.name),
            Tool(name=TaskTrackerTool.name),
            Tool(name=TerminalTool.name),
        ]

        agent = Agent(
            llm=llm,
            tools=tools,
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