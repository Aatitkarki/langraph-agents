import uuid
from typing import Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import Runnable

# Import the shared state definition
from .state import FinancialAgentState

def create_worker_node_finance(agent_name: str, agent: Runnable): # Agent is a Runnable (CompiledGraph)
    """Creates a worker node that invokes the agent and prepares the output."""
    def worker_node(state: FinancialAgentState) -> Dict[str, List[BaseMessage]]:
        print(f"---Worker Node: {agent_name} Running---")
        result = agent.invoke(state) # The agent runnable handles its own state/message management

        # The result from create_react_agent should contain the final AIMessage in 'messages'
        last_agent_message = result["messages"][-1]
        content_to_format = ""

        # Extract content, prioritizing AIMessage
        if isinstance(last_agent_message, AIMessage):
             content_to_format = last_agent_message.content
        elif isinstance(last_agent_message, (HumanMessage, ToolMessage)): # Handle cases where agent might return tool/human msg last
             content_to_format = last_agent_message.content
        else:
             content_to_format = str(last_agent_message) # Fallback

        # Wrap the final response in a HumanMessage with the agent's name
        # This helps the supervisor know who last spoke.
        formatted_message = HumanMessage(
            content=content_to_format, name=agent_name, id=str(uuid.uuid4())
        )
        print(f"---Worker Node: {agent_name} Finished---")
        # Return the formatted message to be appended to the state
        return {"messages": [formatted_message]}
        # Worker returns its output; supervisor decides the next step based on this.
    return worker_node