import os # Add os import back for getenv
from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
# Import constants
from constants import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL_NAME, LANGFUSE_HANDLER

# Constants are loaded from constants.py (which loads from .env)
# --- State Definition ---
class State(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: The list of messages accumulated so far. The `add_messages` function
                  ensures that new messages are appended rather than overwriting the list.
    """
    messages: Annotated[list, add_messages]

# --- Graph Definition ---
graph_builder = StateGraph(State)

# --- LLM and Node Definition ---
# Initialize the OpenAI LLM using constants
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
)

def chatbot(state: State):
    """
    The core chatbot node. Invokes the LLM with the current state's messages
    and returns the LLM's response to be added to the messages list.
    """
    print("---LLM INVOKED---")
    return {"messages": [llm.invoke(state["messages"])]}

# Add the chatbot node to the graph
graph_builder.add_node("chatbot", chatbot)

# --- Graph Structure ---
# Set the entry point: the first node to be called
graph_builder.add_edge(START, "chatbot")

# Set the finish point: specify when the graph execution should end
graph_builder.add_edge("chatbot", END)

# --- Compile the Graph ---
graph = graph_builder.compile().with_config({"callbacks": [LANGFUSE_HANDLER]})

# --- Visualization (Optional) ---
# You can uncomment the following lines to visualize the graph if you have
# the necessary dependencies (like mermaid-cli or pygraphviz) installed.
# from IPython.display import Image, display
# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     print("Graph visualization requires additional dependencies.")

# --- Interaction Loop ---
if __name__ == "__main__":
    print("\nBasic LangGraph Chatbot")
    print("Enter 'quit', 'exit', or 'q' to end the chat.")
    print("-" * 30)

    config = {"configurable": {"thread_id": "basic-chat-1"}} # Example thread_id

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # Stream the graph execution
        # stream_mode="values" yields the full state after each step
        events = graph.stream(
            {"messages": [("user", user_input)]}, # Input is a list of tuples (role, content) or BaseMessages
            config=config,
            stream_mode="values",
        )
        for event in events:
            print("Got Event :",event)
            # The event value is the State dictionary
            # We print the last message added, which is the AI's response
            event["messages"][-1].pretty_print()