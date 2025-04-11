import os
from typing import Annotated, List, Sequence
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.tools import tool # Import tool decorator if needed for custom tools
from langchain_core.runnables import RunnableConfig
import json

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Import constants
from constants import (
    llm,
    TAVILY_API_KEY,
    LANGFUSE_HANDLER
)


# --- Environment Setup ---
# Constants are loaded from constants.py
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not set. Search tool may not function.")

# --- State Definition ---
class State(TypedDict):
    """
    Represents the state of our graph.
    Attributes:
        messages: The list of messages accumulated so far.
        search_results: A list to store results from the search tool.
    """
    messages: Annotated[list, add_messages]
    # NEW: Add a field to store search results
    search_results: List[dict]

# --- Tool Definition ---
# Use the imported constant for the API key
tavily_tool = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY)
tools = [tavily_tool]

# --- Graph Definition ---
graph_builder = StateGraph(State)

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """Chatbot node: Invokes LLM with tools."""
    print("---LLM INVOKED---")
    # Important: We need to clear previous search results before the LLM call
    # if we only want results from the *current* turn to be stored.
    # Alternatively, manage accumulation if needed.
    state_update = {"search_results": []} # Clear previous results for this example
    response = llm_with_tools.invoke(state["messages"])
    state_update["messages"] = [response]
    return state_update


# MODIFIED ToolNode: We wrap the prebuilt ToolNode to capture its output
# This is one way to get tool results into the main state.
# Another approach could be a custom tool node or modifying the tool itself.
def tool_node_wrapper(state: State):
    """Executes tools and captures results."""
    print("---TOOLS INVOKED---")
    tool_node = ToolNode(tools=tools)
    # Invoke the prebuilt ToolNode
    tool_messages: Sequence[BaseMessage] = tool_node.invoke(state)

    # Capture search results if they exist in the tool messages
    # This assumes Tavily returns results as content in a ToolMessage
    # and we might need to parse it (e.g., if it's JSON string)
    current_search_results = []
    for msg in tool_messages:
        if isinstance(msg, ToolMessage) and msg.name == tavily_tool.name:
            # Assuming the content is directly the list of results or needs parsing
            results = None # Initialize results
            if isinstance(msg.content, str):
                try:
                    # Attempt to parse if it's a string
                    results = json.loads(msg.content)
                except json.JSONDecodeError:
                    # Handle cases where the string is not valid JSON
                    print(f"Warning: Could not decode JSON from tool message content: {msg.content}")
                    # Optionally, you could try to handle non-JSON strings differently here
            elif isinstance(msg.content, list):
                # If it's already a list, use it directly
                results = msg.content
            else:
                # Handle other unexpected types if necessary
                print(f"Warning: Unexpected type for tool message content: {type(msg.content)}")

            # Ensure results is a list before extending
            if isinstance(results, list):
                current_search_results.extend(results)
            else: # Or just store the raw content if unsure
                # This assumes that if results is not a list after processing,
                # we might want to store the original content for debugging or other purposes.
                # Consider if this is the desired behavior.
                # If msg.content was not a string or list initially, results would be None here.
                # If msg.content was a string but not valid JSON, results would be None.
                # If msg.content was already a list, results would be that list, and this else wouldn't trigger.
                if results is None and msg.content is not None: # Check if parsing failed or type was unexpected
                     current_search_results.append({"raw_content": msg.content})


    return {"messages": tool_messages, "search_results": current_search_results}


graph_builder.add_node("chatbot", chatbot)
# Use the wrapper node instead of the direct ToolNode
graph_builder.add_node("tools", tool_node_wrapper)

# --- Graph Structure ---
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")

# --- Compile the Graph with Checkpointer ---
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# --- Interaction Loop ---
if __name__ == "__main__":
    print("LangGraph Chatbot with Custom State (Search Results)")
    print("Enter 'quit', 'exit', or 'q' to end the chat.")
    print("-" * 30)

    thread_id = "custom-state-chat-1"
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    print(f"Using conversation thread_id: {thread_id}")

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
        last_state = None
        for event in events:
            if "messages" in event:
                 event["messages"][-1].pretty_print()
            last_state = event # Keep track of the last state

        # After the stream finishes, print the captured search results from the last state
        if last_state and last_state.get("search_results"):
            print("\n--- Captured Search Results ---")
            import json # For pretty printing
            print(json.dumps(last_state["search_results"], indent=2))
            print("-----------------------------")