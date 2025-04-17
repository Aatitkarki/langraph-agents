import logging
from typing import Callable, Literal, Type
from pydantic import BaseModel, create_model

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import END
from langgraph.types import Command

# Import the shared state definition
from .state import FinancialAgentState

logger = logging.getLogger(f"{__name__}")

def create_supervisor_finance(
    llm: BaseChatModel,
    members: list[str]
) -> Callable[[FinancialAgentState], dict]: # Changed return type from Command to dict
    """Creates a supervisor node function for routing between financial agents.
    
    This function generates a LangGraph supervisor node that orchestrates routing between
    specialized financial agents based on the conversation history and user query.
    The supervisor uses an LLM to analyze the conversation and determine the next
    appropriate agent or whether to terminate the workflow.

    Args:
        llm (BaseChatModel): The language model instance to use for routing decisions.
        members (list[str]): List of available agent names that can be routed to.

    Returns:
        Callable[[FinancialAgentState], dict]: A supervisor node function that:
            - Takes FinancialAgentState as input
            - Returns a dictionary containing state updates, including the 'next'
              field which determines routing via the conditional edge function.
    """
    options = ["FINISH"] + members
    # system_prompt = (
    #     "You are a financial assistant supervisor. Your job is to understand the user's financial query "
    #     "and route it to the correct specialist agent, or handle general inquiries.\n"
    #     f"The available specialists and their functions are:\n"
    #     f"- account_agent: Handles queries about account summaries (balance, type).\n"
    #     f"- transaction_agent: Handles queries about transaction history.\n"
    #     f"- card_agent: Handles queries about credit card details (limit, balance, due date).\n"
    #     f"- exchange_rate_agent: Handles queries about currency exchange rates and performs conversions.\n\n"
    #     "Based on the user's request and the conversation history, choose the single next specialist agent to act.\n"
    #     "If the user asks a general question about capabilities (like 'what can you do?'), respond with 'FINISH' but first provide a brief summary of the available specialists and their functions in your reasoning process (this summary won't be shown to the user, but helps guide your decision). \n"
    #     "If the query has been fully answered by previous agents or cannot be answered by any specialist, respond with 'FINISH'.\n"
    #     f"Respond ONLY with the name of the next specialist agent ({', '.join([f'{m}' for m in members])}) or 'FINISH'." # Dynamically list members
    #     "Do not add any other explanation to your final output."
    # )
    system_prompt = (
        "You are a financial assistant supervisor. Your job is to orchestrate specialist agents to fulfill the user's financial query.\n"
        "Review the **entire conversation history** below, paying close attention to the **most recent message**.\n\n"
        f"The available specialists and their functions are:\n"
        f"- account_agent: Handles queries about account summaries (balance, type).\n"
        f"- transaction_agent: Handles queries about transaction history.\n"
        f"- card_agent: Handles queries about credit card details (limit, balance, due date).\n"
        f"- exchange_rate_agent: Handles queries about currency exchange rates and performs conversions.\n\n"
        "**Your Decision Process:**\n"
        "1. Examine the **original user request** and the **latest message** in the history.\n"
        "2. **If the latest message is from a specialist agent:** Does it directly and completely answer the specific task assigned to that agent?\n"
        "   - **If YES, and no other parts of the original user query remain unaddressed** by other specialists, respond with 'FINISH'. The specialist's last message contains the final answer.\n"
        "   - **If YES, but other parts of the original query still need a *different* specialist**, route to the appropriate next specialist.\n"
        "   - **If NO (the specialist couldn't answer or needs more info not available)**, decide if another specialist can help or if the query is unresolvable. Route to the next specialist or respond 'FINISH' if no further progress can be made.\n"
        "3. **If the latest message is from the user:** Determine which specialist is best suited to handle the newest request based on their capabilities. Route to that specialist.\n"
        "4. **General Queries:** If the user asks a general question about capabilities (like 'what can you do?'), respond with 'FINISH' but first provide a brief summary of the available specialists and their functions in your reasoning process (this summary won't be shown to the user, but helps guide your decision). \n"
        "5. **Completion:** If the query has been fully resolved by the history, or if no specialist can address the remaining request, respond with 'FINISH'.\n\n"
        f"**Output Format:** Respond with a JSON object containing two fields: 'next' (the name of the single next specialist agent ({', '.join([f'{m}' for m in members])}) or 'FINISH') and 'message'. If 'next' is 'FINISH', the 'message' should be the final response to the user summarizing the outcome. If 'next' is an agent, the 'message' should be a brief summary of the current state or reasoning for routing."
    )

    # Dynamically create the Pydantic model for the router
    Router: Type[BaseModel] = create_model(
        'Router',
        next=(Literal[tuple(options)], ...),
        message=(str, ...) # Renamed summary to message
        # Config removed as title/description might not be needed for with_structured_output here
    )

    supervisor_chain = llm.with_structured_output(Router, include_raw=False)

    def supervisor_node(state: FinancialAgentState) -> dict: # Changed return type from Command to dict
        """Routes work to the appropriate worker or finishes the workflow.
        
        The supervisor node analyzes the conversation history and current state to:
        1. Determine if the query has been fully answered
        2. Identify which specialist agent should handle the next step
        3. Generate appropriate routing commands

        Args:
            state (FinancialAgentState): The current workflow state containing:
                - messages: The conversation history
                - other agent-specific state data

        Returns:
            dict: A dictionary containing state updates. The 'next' key in this
                  dictionary will be used by the conditional edge logic in the
                  graph builder to determine the next node.
        """
        logger.debug("---Supervisor Running---")
        # Supervisor decides based on the conversation history
        # # Filter out tool messages for brevity if needed for the supervisor LLM call
        # supervisor_input_messages = [m for m in state['messages'] if not isinstance(m, ToolMessage)]
        supervisor_input_messages = state['messages']
        supervisor_input_messages = [SystemMessage(content=system_prompt)] + supervisor_input_messages

        logger.debug(f"input to llm: {supervisor_input_messages}")
        response = supervisor_chain.invoke(supervisor_input_messages)
        logger.debug(f"response from llm: {response}")

        message = "No message provided." # Default message
        next_worker = "FINISH" # Default next worker

        # Explicitly check the type before accessing the attribute
        if isinstance(response, Router):
            next_worker = getattr(response, 'next', 'FINISH') # Use getattr as a fallback access method
            message = getattr(response, 'message', message) # Extract message
        else:
            # Fallback if the response is not the expected Pydantic model
            logger.warning(f"Supervisor response type unexpected. Type: {type(response)}, Value: {response}")
            # Attempt dictionary access or default to FINISH
            try:
                if isinstance(response, dict):
                    next_worker = response.get("next", "FINISH")
                    message = response.get("message", message)
                else:
                     next_worker = "FINISH"
            except Exception:
                 logger.error("Could not determine next worker or message from supervisor response.")
                 next_worker = "FINISH" # Default to FINISH on error

        logger.info(f"---Supervisor Message/Reasoning: {message}---") # Log the message/reasoning
        logger.info(f"---Supervisor Decision: Route to {next_worker}---")
        if next_worker == "FINISH":
            # Add the final message to the state before finishing
            # Return state update indicating finish. The routing function handles mapping this to END.
            # The supervisor's 'message' is logged for reasoning, not added to state here.
            return {"next": "FINISH"}
        else:
            # Ensure the chosen worker is actually in the members list before routing
            if next_worker in members:
                 # Return state update indicating the next worker
                return {"next": next_worker}
            else:
                logger.warning(f"Error: Supervisor chose invalid worker '{next_worker}'. Defaulting to FINISH.")
                 # Return state update indicating finish if worker is invalid
                return {"next": "FINISH"}
    return supervisor_node