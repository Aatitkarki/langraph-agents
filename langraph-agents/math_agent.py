import operator
from typing import Annotated, Sequence, TypedDict
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool # Import tool decorator
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode # We can still use ToolNode for custom tools

from constants import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL_NAME,LANGFUSE_HANDLER

@tool
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    print(f"--- Running Addition Tool: {a} + {b} ---")
    return operator.add(a, b)

@tool
def subtract(a: int, b: int) -> int:
    """Subtracts the second number from the first."""
    print(f"--- Running Subtraction Tool: {a} - {b} ---")
    return operator.sub(a, b)

# List of custom tools
tools = [add, subtract]

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# --- Graph Definition ---
graph_builder = StateGraph(AgentState)

# --- LLM and Node Definition ---
# Initialize LLM using constants
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
)

# Bind the custom tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# Define the node that calls the model
def call_model(state: AgentState):
    """Invokes the LLM with the current state messages and tools."""
    print("---LLM INVOKED (Math Agent)---")
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# Define the node to execute tools
# We can use the prebuilt ToolNode with our custom tools
tool_node = ToolNode(tools=tools)

# --- Graph Structure ---
graph_builder.add_node("llm", call_model)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "llm")

# Conditional routing: Does the LLM response contain tool calls?
def should_continue(state: AgentState):
    """Determines whether to continue to tools or end."""
    messages = state['messages']
    last_message = messages[-1]
    # If there are no tool calls, then we finish
    if not last_message.tool_calls:
        return END
    # Otherwise if there are tool calls, we call the tools node
    else:
        return "tools"

graph_builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

# After tools are invoked, return control to the LLM
graph_builder.add_edge("tools", "llm")

# --- Compile the Graph ---
# Using MemorySaver for conversation history (optional but good practice)
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory).with_config({
    "callbacks": [LANGFUSE_HANDLER],
})

# --- Interaction Loop ---
if __name__ == "__main__":
    print("LangGraph Math Agent with Custom Tools")
    print("Ask math questions like 'What is 5 + 3?' or 'Calculate 10 - 4'.")
    print("Enter 'quit', 'exit', or 'q' to end the chat.")
    print("-" * 30)

    thread_id = "math-agent-1"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Using conversation thread_id: {thread_id}")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        events = graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="values",
        )
        for event in events:
            if "messages" in event:
                 # Print only the last message if it's an AIMessage without tool calls
                 last_message = event["messages"][-1]
                 if isinstance(last_message, AIMessage) and not last_message.tool_calls:
                     last_message.pretty_print()