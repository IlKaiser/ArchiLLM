from typing import ClassVar, Any, Sequence

from pydantic import model_validator
import copy

from openhands.sdk.llm.message import Message
from openhands.sdk.llm.llm_response import LLMResponse
from openhands.sdk.llm.router.base import RouterLLM
from openhands.sdk.tool.tool import ToolDefinition
from openhands.sdk.llm.streaming import TokenCallbackType
from openhands.sdk.logger import get_logger

logger = get_logger(__name__)


class EffortRouter(RouterLLM):
    """
    A RouterLLM implementation that routes requests based on the effort required.
    High effort requests (like complex code logic, deep planning) are routed to 
    the primary model, while simple tool calls or straightforward responses are 
    routed to the secondary model.
    """

    router_name: str = "effort_router"

    PRIMARY_MODEL_KEY: ClassVar[str] = "primary"
    SECONDARY_MODEL_KEY: ClassVar[str] = "secondary"

    def completion(
        self,
        messages: list[Message],
        tools: Sequence[ToolDefinition] | None = None,
        return_metrics: bool = False,
        add_security_risk_prediction: bool = False,
        on_token: TokenCallbackType | None = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Overrides the RouterLLM completion to sanitize `thinking_blocks` 
        for models that don't support them.
        """
        selected_model = self.select_llm(messages)
        self.active_llm = self.llms_for_routing[selected_model]

        logger.info(f"EffortRouter routing to {selected_model}...")

        # Sanitize messages if routing to secondary model
        if selected_model == self.SECONDARY_MODEL_KEY:
            sanitized_messages = []
            
            i = 0
            while i < len(messages):
                msg = messages[i]
                msg_copy = copy.copy(msg)
                
                # Devstral/Mistral rejects the 'thinking_blocks' key in the litellm dict
                if hasattr(msg_copy, 'thinking_blocks') and msg_copy.thinking_blocks:
                    msg_copy.thinking_blocks = []
                
                # If there are multiple tool calls, split them up
                if msg_copy.role == "assistant" and getattr(msg_copy, 'tool_calls', None) and len(msg_copy.tool_calls) > 1:
                    tool_calls = msg_copy.tool_calls
                    
                    # Look ahead for corresponding tool response messages
                    j = i + 1
                    tool_responses = {}
                    while j < len(messages) and messages[j].role == "tool":
                        tool_responses[messages[j].tool_call_id] = messages[j]
                        j += 1
                        
                    for idx, tc in enumerate(tool_calls):
                        new_ast_msg = copy.copy(msg_copy)
                        new_ast_msg.tool_calls = [tc]
                        if idx > 0:
                            new_ast_msg.content = []  # Only keep text content in the first one
                        sanitized_messages.append(new_ast_msg)
                        
                        if tc.id in tool_responses:
                            # Add the corresponding tool response message directly after
                            sanitized_messages.append(copy.copy(tool_responses[tc.id]))
                            
                    i = j  # Skip over the tool messages we just intertwined
                else:
                    sanitized_messages.append(msg_copy)
                    i += 1
                    
            messages_to_send = sanitized_messages
        else:
            messages_to_send = messages

        # Delegate to selected LLM
        return self.active_llm.completion(
            messages=messages_to_send,
            tools=tools,
            _return_metrics=return_metrics,
            add_security_risk_prediction=add_security_risk_prediction,
            on_token=on_token,
            **kwargs,
        )

    def select_llm(self, messages: list[Message]) -> str:
        """Select LLM based on perceived effort/complexity of the request."""
        route_to_primary = False

        if not messages:
            return self.SECONDARY_MODEL_KEY

        latest_message = messages[-1]

        # Heuristic 1: If the secondary model context is exceeded, go to primary
        secondary_llm = self.llms_for_routing.get(self.SECONDARY_MODEL_KEY)
        if secondary_llm and getattr(secondary_llm, 'max_input_tokens', None):
            if secondary_llm.get_token_count(messages) > secondary_llm.max_input_tokens:
                logger.warning(
                    f"Messages exceeded secondary model's max input tokens. "
                    "Routing to the primary model."
                )
                route_to_primary = True

        # Heuristic 2: Check for multimodal content (usually requires primary)
        for message in messages:
            if getattr(message, "contains_image", False):
                logger.info("Multimodal content detected. Routing to the primary model.")
                route_to_primary = True
                break

        # Heuristic 3: Analyze the text content for "high effort" indicators
        high_effort_keywords = [
            "implement", "architect", "design", "refactor", "algorithm",
            "complex logic", "debug", "explain", "analyze"
        ]

        if not route_to_primary and hasattr(latest_message, 'content'):
            content_str = str(latest_message.content).lower()
            if any(keyword in content_str for keyword in high_effort_keywords):
                logger.info("High effort request detected based on keywords. Routing to primary model.")
                route_to_primary = True

        if route_to_primary:
            return self.PRIMARY_MODEL_KEY
        else:
            return self.SECONDARY_MODEL_KEY

    @model_validator(mode="after")
    def _validate_llms_for_routing(self) -> "EffortRouter":
        """Ensure required models are present in llms_for_routing."""
        if self.PRIMARY_MODEL_KEY not in self.llms_for_routing:
            raise ValueError(
                f"Primary LLM key '{self.PRIMARY_MODEL_KEY}' not found in llms_for_routing."
            )
        if self.SECONDARY_MODEL_KEY not in self.llms_for_routing:
            raise ValueError(
                f"Secondary LLM key '{self.SECONDARY_MODEL_KEY}' not found in llms_for_routing."
            )
        return self
