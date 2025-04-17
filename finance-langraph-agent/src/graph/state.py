from typing import Optional, List, Dict, Any
from typing import Optional
from langgraph.graph import MessagesState

# --- Shared State Definition ---
class FinancialAgentState(MessagesState):
    """The shared state for financial agent workflows.
    
    Extends LangGraph's MessagesState to track conversation history and adds:
    - Routing information between agents
    - Workflow control state
    - Streaming buffer for real-time output
    - Error context for robust handling
    - Flag for human intervention points
    Extends LangGraph's MessagesState to track conversation history and adds:
    - Routing information between agents
    - Workflow control state

    Inherits from MessagesState which provides:
    - messages: List[BaseMessage] - The conversation history

    Attributes:
        messages: List[BaseMessage] - Inherited conversation history.
        next (Optional[str]): Controls workflow routing (agent name, 'FINISH', or None).
        streaming_buffer (Optional[List[str]]): Holds chunks of streamed output.
        error_context (Optional[Dict[str, Any]]): Stores details of errors encountered.
        human_intervention_required (bool): Flag indicating if human input is needed.
    Attributes:
        next (Optional[str]): Controls workflow routing with possible values:
            - None: Initial state or workflow complete
            - "FINISH": Signals workflow should terminate
            - [agent_name]: Name of next agent to route to (e.g. "account_agent")
    """
    next: Optional[str]  # Stores the name of the next agent to route to, or None/FINISH
    # New attributes for enhanced features
    streaming_buffer: Optional[List[str]]
    error_context: Optional[Dict[str, Any]]
    human_intervention_required: bool