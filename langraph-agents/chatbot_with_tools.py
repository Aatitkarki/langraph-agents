from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage # Needed for type hints potentially

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition # Import prebuilt nodes
# Import constants
from constants import (
    LANGFUSE_HANDLER,
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_MODEL_NAME,
    TAVILY_API_KEY,
    
)

# --- Environment Setup ---
# Constants are loaded from constants.py (which loads from .env)
# Ensure TAVILY_API_KEY is set in your .env file or environment
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not set. Search tool may not function.")

# --- State Definition ---
class State(TypedDict):
    """
    Represents the state of our graph. Includes messages list.
    """
    messages: Annotated[list, add_messages]

# --- Tool Definition ---
# max_results=2 limits the search results for brevity
# Use the imported constant for the API key
tool = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY)
tools = [tool]

# --- Graph Definition ---
graph_builder = StateGraph(State)

# --- LLM and Node Definition ---
# Initialize the OpenAI LLM using constants
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
)

# Bind the tools to the LLM.
# This allows the LLM to generate structured tool calls.
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """
    Chatbot node: Invokes LLM with tools.
    """
    print("---LLM INVOKED---")
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Add the chatbot node
graph_builder.add_node("chatbot", chatbot)

# Add the prebuilt ToolNode. This executes tools based on the last message.
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# --- Graph Structure ---
# Set the entry point
graph_builder.add_edge(START, "chatbot")

# Add the conditional edge.
# Route to 'tools' if the chatbot function generated tool calls, otherwise route to END.
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition, # Prebuilt condition checks for tool calls
    # Mapping: "tools" routes to the 'tools' node, END routes to the special END node
    {"tools": "tools", END: END},
)

# Add an edge from the tools node back to the chatbot node.
# This allows the chatbot to process the tool results.
graph_builder.add_edge("tools", "chatbot")

# --- Compile the Graph ---
graph = graph_builder.compile().with_config({
    "callbacks": [LANGFUSE_HANDLER],
})

# --- Visualization (Optional) ---
# from IPython.display import Image, display
# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     print("Graph visualization requires additional dependencies.")

# --- Interaction Loop ---
if __name__ == "__main__":
    print("LangGraph Chatbot with Tools")
    print("Enter 'quit', 'exit', or 'q' to end the chat.")
    print("-" * 30)

    config = {"configurable": {"thread_id": "tools-chat-1"}}

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        events = graph.stream(
            {"messages": [("user", user_input)]},
            config=config,
            stream_mode="values",
        )
        for event in events:
            # Check if the event is from the chatbot or the tool node
            if "messages" in event:
                 event["messages"][-1].pretty_print()