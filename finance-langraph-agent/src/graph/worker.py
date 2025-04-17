import logging
from typing import Callable
from typing_extensions import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable

from langgraph.types import Command
# Import the shared state definition
from .state import FinancialAgentState

def create_worker_node_finance(
    agent_name: str,
    agent: Runnable
) -> Callable[[FinancialAgentState], dict]: # Changed return type from Command to dict
    """Creates a worker node function that executes a financial agent and routes back to supervisor.
    
    This factory function generates a LangGraph worker node that:
    1. Invokes the specified agent with the current state
    2. Processes the agent's response
    3. Returns a command to route back to the supervisor

    Args:
        agent_name (str): Name of the agent (used for logging and message attribution)
        agent (Runnable): The agent runnable to execute when this worker is activated

    Returns:
        Callable[[FinancialAgentState], dict]: A worker node function that:
            - Takes FinancialAgentState as input
            - Returns a dictionary containing the state updates (e.g., new messages)
    """

    logger = logging.getLogger(f"{__name__} {agent_name}")

    def worker_node(state: FinancialAgentState) -> dict: # Changed return type from Command to dict
        """Executes the agent and prepares its output for the workflow.
        
        The worker node:
        1. Invokes the assigned agent with the current state
        2. Extracts the agent's response message
        3. Formats the response for the workflow
        4. Returns a command to route back to supervisor

        Args:
            state (FinancialAgentState): The current workflow state containing:
                - messages: The conversation history
                - other agent-specific state data

        Returns:
            dict: A dictionary containing the state update, typically the agent's
                  response message to be added to the history. Routing back to
                  the supervisor is handled by the graph's static edges.
        """
        logger.debug(f"---Worker Node: {agent_name} Running---")
        result = agent.invoke(state) # The agent runnable handles its own state/message management

        # The result from create_react_agent should contain the final AIMessage in 'messages'
        last_agent_message = result["messages"][-1]
        logger.debug(f"Worker agent message: {last_agent_message}")
        # Return the state update dictionary. The graph structure handles routing back.
        return {
            "messages": [
                AIMessage(content=last_agent_message.content, name=agent_name)
            ]
        }

    return worker_node