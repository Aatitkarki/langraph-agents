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
) -> Callable[[FinancialAgentState], Command[Literal["supervisor"]]]:
    """Creates a worker node function that executes a financial agent and routes back to supervisor.
    
    This factory function generates a LangGraph worker node that:
    1. Invokes the specified agent with the current state
    2. Processes the agent's response
    3. Returns a command to route back to the supervisor

    Args:
        agent_name (str): Name of the agent (used for logging and message attribution)
        agent (Runnable): The agent runnable to execute when this worker is activated

    Returns:
        Callable[[FinancialAgentState], Command[Literal["supervisor"]]]: A worker node function that:
            - Takes FinancialAgentState as input
            - Returns a Command directing the workflow back to the supervisor
    """

    logger = logging.getLogger(f"{__name__} {agent_name}")

    def worker_node(state: FinancialAgentState) -> Command[Literal["supervisor"]]:
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
            Command[Literal["supervisor"]]: Always routes back to supervisor with:
                - The agent's response message
                - Metadata identifying the responding agent
        """
        logger.debug(f"---Worker Node: {agent_name} Running---")
        result = agent.invoke(state) # The agent runnable handles its own state/message management

        # The result from create_react_agent should contain the final AIMessage in 'messages'
        last_agent_message = result["messages"][-1]
        logger.debug(f"Worker agent message: {last_agent_message}")
        return Command(
        update={
            "messages": [
                AIMessage(content=last_agent_message.content, name=agent_name)
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
        )

    return worker_node