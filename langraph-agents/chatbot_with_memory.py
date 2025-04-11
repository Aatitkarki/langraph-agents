from email.mime import base
from typing import Annotated
from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver # Import MemorySaver
# Import constants
from constants import (
    llm,
    TAVILY_API_KEY,
    LANGFUSE_HANDLER
)

# --- State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- Tool Definition ---
# Use the imported constant for the API key
tool = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY)
tools = [tool]

# --- Graph Definition ---
graph_builder = StateGraph(State)

# --- LLM and Node Definition ---
# Initialize the OpenAI LLM using constants
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    print("---LLM INVOKED---")
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# --- Graph Structure ---
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")

# --- Compile the Graph with Checkpointer ---
# Instantiate an in-memory checkpointer
memory = MemorySaver()

# Compile the graph with the checkpointer
# This enables persistence.
graph = graph_builder.compile(checkpointer=memory)

# --- Visualization (Optional) ---
# from IPython.display import Image, display
# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     print("Graph visualization requires additional dependencies.")

# --- Interaction Loop ---
if __name__ == "__main__":
    print("LangGraph Chatbot with Tools and Memory")
    print("Enter 'quit', 'exit', or 'q' to end the chat.")
    print("You can start a new conversation thread by changing the thread_id.")
    print("-" * 30)

    # Define a thread_id for the conversation
    # All interactions with the same thread_id will share memory.
    thread_id = "memory-chat-1"
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    print(f"Using conversation thread_id: {thread_id}")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # Pass the config to stream/invoke to maintain state
        events = graph.stream(
            {"messages": [("user", user_input)]},
            config=config,
            stream_mode="values",
        )
        for event in events:
            if "messages" in event:
                 event["messages"][-1].pretty_print()