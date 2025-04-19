from typing import Optional, List, Dict, Any
from typing import Optional
from langgraph.graph import MessagesState

# --- Shared State Definition ---
class FinancialAgentState(MessagesState):
    """The shared state for financial agent workflows.

    Extends LangGraph's MessagesState to track conversation history and adds
    attributes for routing, streaming, error handling, human intervention,
    and RAG context.

    Inherits from MessagesState which provides:
    - messages: List[BaseMessage] - The conversation history

    Attributes:
        messages: List[BaseMessage] - Inherited conversation history.
        next (Optional[str]): Controls workflow routing with possible values:
            - None: Initial state or workflow complete
            - "FINISH": Signals workflow should terminate
            - [agent_name]: Name of next agent to route to (e.g. "account_agent")
        streaming_buffer (Optional[List[str]]): Holds chunks of streamed output.
        error_context (Optional[Dict[str, Any]]): Stores details of errors encountered.
        human_intervention_required (bool): Flag indicating if human input is needed.
        rag_context (Optional[str]): Stores context retrieved from the RAG system.
    """
    next: Optional[str]
    streaming_buffer: Optional[List[str]]
    error_context: Optional[Dict[str, Any]]
    human_intervention_required: bool
    rag_context: Optional[str] # Context retrieved from RAG