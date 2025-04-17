import logging
from langgraph.graph import Graph, START, END
from langgraph.checkpoint.memory import InMemorySaver # Changed InMemorySaver to SQLiteSaver
from typing import Literal, Dict, Hashable

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.agents import agent_names, agent_map # Import names and agent runnables
from .state import FinancialAgentState
from .supervisor import create_supervisor_finance
from .worker import create_worker_node_finance

logger = logging.getLogger(f"{__name__}")

# --- Graph Definition ---
logger.debug("--- Building Finance Agent Graph ---")
finance_builder = Graph() # Changed StateGraph to Graph

# --- Define Routing Function ---
# Assuming agent_names = ['account_agent', 'transaction_agent', 'card_agent', 'exchange_rate_agent']
# The actual names from src.agents should be used here.
def route_from_supervisor(state: FinancialAgentState) -> str: # Changed return type hint to str
    """Determines the next node based on the 'next' value in the state."""
    next_node = state.get('next') # Use .get for safety
    logger.debug(f"Routing from supervisor. Next node determined: {next_node}")
    if next_node in agent_names:
        return next_node
    elif next_node == "FINISH":
        return END # Use the imported END constant
    else:
        # Handle unexpected case, maybe default to END or raise error
        logger.warning(f"Unexpected 'next' value in state: {next_node}. Routing to END.")
        return END

# --- Define Nodes ---
# Supervisor Node
supervisor_node_finance = create_supervisor_finance(llm, agent_names)
finance_builder.add_node("supervisor", supervisor_node_finance)

# Worker Nodes (using the map from agents/__init__.py)
for name, agent_runnable in agent_map.items():
    worker_node = create_worker_node_finance(name, agent_runnable)
    finance_builder.add_node(name, worker_node)

# 2. Define Edges
# Set the entry point
finance_builder.set_entry_point("supervisor")

# Workers go back to supervisor
for name in agent_names:
    finance_builder.add_edge(name, "supervisor")

# Supervisor routes to workers or END using conditional edges
# The routing function `route_from_supervisor` dictates the path.
# Create a mapping from the routing function's output string literal to the target node names.
node_mapping: Dict[Hashable, str] = {name: name for name in agent_names} # Added type hint
# Use the string literal "__end__" as the key, mapping it to the END constant for the graph.
node_mapping["__end__"] = END

finance_builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    node_mapping
)

# --- Compile the graph with persistent checkpointing ---
# Using SQLite for persistence. ":memory:" can be replaced with a file path e.g., "checkpoints.sqlite"
memory = InMemorySaver()
finance_graph = finance_builder.compile(checkpointer=memory)
logger.debug("--- Finance Agent Graph Compiled Successfully with SQLite Checkpointer! ---")