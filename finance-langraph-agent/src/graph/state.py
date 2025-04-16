from typing import Optional
from langgraph.graph import MessagesState

# --- Shared State Definition ---
class FinancialAgentState(MessagesState):
    """The shared state for financial agent workflows.
    
    Extends LangGraph's MessagesState to track conversation history and adds:
    - Routing information between agents
    - Workflow control state

    Inherits from MessagesState which provides:
    - messages: List[BaseMessage] - The conversation history

    Attributes:
        next (Optional[str]): Controls workflow routing with possible values:
            - None: Initial state or workflow complete
            - "FINISH": Signals workflow should terminate
            - [agent_name]: Name of next agent to route to (e.g. "account_agent")
    """
    next: Optional[str]  # Stores the name of the next agent to route to, or None/FINISH