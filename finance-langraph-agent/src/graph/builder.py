import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# Import necessary components from other modules
from src.utils.llm_config import supervisor_llm
from src.agents import agent_names, agent_map # Import names and agent runnables
from .state import FinancialAgentState
from .supervisor import create_supervisor_finance
from .worker import create_worker_node_finance

logger = logging.getLogger(f"{__name__}")

# --- Graph Definition ---
logger.debug("--- Building Finance Agent Graph ---")
finance_builder = StateGraph(FinancialAgentState)

# 1. Define Nodes
# Supervisor Node
supervisor_node_finance = create_supervisor_finance(supervisor_llm, agent_names)
finance_builder.add_node("supervisor", supervisor_node_finance)

# Worker Nodes (using the map from agents/__init__.py)
for name, agent_runnable in agent_map.items():
    worker_node = create_worker_node_finance(name, agent_runnable)
    finance_builder.add_node(name, worker_node)

# 2. Define Edges
# Start goes to supervisor
finance_builder.add_edge(START, "supervisor")

# Workers go back to supervisor
# for name in agent_names:
#     finance_builder.add_edge(name, "supervisor")

# Supervisor routes to workers or END (handled by Command(goto=...) in supervisor_node)
# No explicit edges needed from supervisor to workers here, conditional routing handles it.

# 3. Compile the graph with memory
memory = InMemorySaver()
finance_graph = finance_builder.compile(checkpointer=memory)
logger.debug("--- Finance Agent Graph Compiled Successfully! ---")
# png_data = finance_graph.get_graph().draw_mermaid_png()
 
# # Save the PNG data to a file
# with open("finance_graph.png", "wb") as f:
#     f.write(png_data)