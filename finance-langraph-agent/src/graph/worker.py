from typing import Callable
from typing_extensions import Literal
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable

from langgraph.types import Command
# Import the shared state definition
from .state import FinancialAgentState

def create_worker_node_finance(agent_name: str, agent: Runnable) -> Callable[[FinancialAgentState], Command[Literal["supervisor"]]]:
    """Creates a worker node that invokes the agent and prepares the output."""
    def worker_node(state: FinancialAgentState) -> Command[Literal["supervisor"]]:
        print(f"---Worker Node: {agent_name} Running---")
        result = agent.invoke(state) # The agent runnable handles its own state/message management

        # The result from create_react_agent should contain the final AIMessage in 'messages'
        last_agent_message = result["messages"][-1]
        return Command(
        update={
            "messages": [
                HumanMessage(content=last_agent_message.content, name=agent_name)
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
        )

    return worker_node 