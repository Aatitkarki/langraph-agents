from typing import Optional
from langgraph.graph import MessagesState

# --- Shared State Definition ---
class FinancialAgentState(MessagesState):
   # MessagesState stores the list of messages (BaseMessage instances)
   # We add 'next' to route control between agents
   next: Optional[str] # Stores the name of the next agent to route to, or None/FINISH