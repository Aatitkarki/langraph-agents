import os
from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# Import constants
from constants import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    OPENAI_MODEL_NAME,
    TAVILY_API_KEY,
)

# --- Environment Setup ---
# Constants are loaded from constants.py
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not set. Search tool may not function.")

# --- State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- Tool Definition ---
tool = TavilySearchResults(max_results=2, tavily_api_key=TAVILY_API_KEY)
tools = [tool]

# --- Graph Definition ---
graph_builder = StateGraph(State)

# --- LLM and Node Definition ---
llm = ChatOpenAI(
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
)
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
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# --- Time Travel Demonstration ---
if __name__ == "__main__":
    print("LangGraph Chatbot - Time Travel Demo")
    print("-" * 30)

    # Define a thread_id for the conversation
    thread_id = "time-travel-chat-1"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Using conversation thread_id: {thread_id}")

    # === Run the graph a few times to build history ===
    print("\n--- Initial Conversation ---")
    initial_inputs = [
        {"messages": [HumanMessage(content="Hi! My name is Bob.")]},
        {"messages": [HumanMessage(content="What's the weather in London?")]},
        {"messages": [HumanMessage(content="Thanks! What about Paris?")]},
    ]

    for i, inp in enumerate(initial_inputs):
        print(f"\nUser: {inp['messages'][0].content}")
        events = graph.stream(inp, config=config, stream_mode="values")
        for event in events:
            if "messages" in event:
                event["messages"][-1].pretty_print()
        print("-" * 10)

    # === Inspect History ===
    print("\n--- Inspecting State History ---")
    history = list(graph.get_state_history(config))
    print(f"Found {len(history)} states in history.")

    # Select a state to replay from (e.g., after the first user message)
    # History is typically ordered newest to oldest. Let's find the state
    # *after* the first LLM response (which should have 2 messages total).
    # Note: State includes intermediate steps (like tool calls), so message count isn't always straightforward.
    # We'll aim for a state roughly after the first exchange.
    # Let's find the state *before* the first tool call (if any) or after the first AI response.
    replay_from_state = None
    target_message_count = 2 # State after first user message and first AI response
    # Iterate from oldest to newest (reverse the list)
    for state in reversed(history):
        # Find the first state that has at least the target message count
        # and represents the end of a turn (next node is START or chatbot)
        if len(state.values['messages']) >= target_message_count and state.next == ('chatbot',):
             replay_from_state = state
             print(f"Selected state to replay from (checkpoint_id: {state.config['configurable']['checkpoint_id']})")
             print("Messages in selected state:")
             for msg in state.values['messages']:
                 msg.pretty_print()
             break # Stop after finding the first suitable state

    if not replay_from_state:
        print("Could not find a suitable state to replay from based on criteria.")
        # As a fallback, maybe pick the second-to-last state if available
        if len(history) >= 2:
             replay_from_state = history[1] # Newest state is history[0]
             print(f"Using fallback state to replay from (checkpoint_id: {replay_from_state.config['configurable']['checkpoint_id']})")


    # === Time Travel - Resume from selected state ===
    if replay_from_state:
        print("\n--- Resuming from Selected State ---")
        # New user input, branching from the past state
        branch_input = {"messages": [HumanMessage(content="Actually, what was my name again?")]}
        print(f"User (branching): {branch_input['messages'][0].content}")

        # Use the config from the selected historical state to resume
        resume_config = replay_from_state.config
        events = graph.stream(branch_input, config=resume_config, stream_mode="values")
        for event in events:
            if "messages" in event:
                event["messages"][-1].pretty_print()

        print("\n--- Checking Final State of Branched Conversation ---")
        final_branched_state = graph.get_state(resume_config)
        print("Messages:")
        for msg in final_branched_state.values['messages']:
            msg.pretty_print()

    print("\n--- Time Travel Demo Complete ---")