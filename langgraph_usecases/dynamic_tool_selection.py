# langgraph_usecases/dynamic_tool_selection.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
# from langchain_openai import ChatOpenAI # Example model
# from langchain_community.vectorstores import ... # For actual retrieval
# from langchain_openai import OpenAIEmbeddings # For actual retrieval

# --- Define Example Tools ---
@tool
def get_weather(location: str):
    """Call to get the current weather in a specific location."""
    if "paris" in location.lower():
        return "It's rainy in Paris."
    elif "tokyo" in location.lower():
        return "It's sunny in Tokyo."
    else:
        return f"Weather data not available for {location}."

@tool
def get_flight_price(departure: str, arrival: str):
    """Call to get the flight price between two cities."""
    return f"Flight from {departure} to {arrival} costs $500."

@tool
def book_hotel(location: str, nights: int):
    """Books a hotel in the specified location for a number of nights."""
    return f"Hotel booked in {location} for {nights} nights."

# --- Full Tool Registry ---
ALL_TOOLS = [get_weather, get_flight_price, book_hotel]
TOOL_MAP = {t.name: t for t in ALL_TOOLS}

# --- State Definition ---
class DynamicToolState(TypedDict):
    """State for an agent that dynamically selects tools."""
    messages: Annotated[List[BaseMessage], add_messages]
    # Store the names of the tools selected for the current step
    selected_tool_names: Optional[List[str]]

# --- Placeholder Models ---
# model = ChatOpenAI(model="gpt-4o-mini")
# tool_retriever = ... # Vector store retriever for tool descriptions

# --- Node Functions ---

def select_tools_node(state: DynamicToolState) -> dict:
    """Selects a subset of tools relevant to the latest user query."""
    print("---TOOL SELECTOR: Selecting relevant tools---")
    last_message = state['messages'][-1]
    query = last_message.content
    print(f"Selecting tools based on query: {query}")

    # Placeholder Logic: Simple keyword matching instead of retrieval
    selected_names = []
    if "weather" in query.lower():
        selected_names.append("get_weather")
    if "flight" in query.lower() or "fly" in query.lower() or "price" in query.lower():
        selected_names.append("get_flight_price")
    if "hotel" in query.lower() or "stay" in query.lower() or "book" in query.lower():
        selected_names.append("book_hotel")

    # Fallback if no tools match
    if not selected_names:
         print("No specific tools matched, selecting all.")
         selected_names = list(TOOL_MAP.keys()) # Or maybe just a default subset

    print(f"Selected tools: {selected_names}")
    return {"selected_tool_names": selected_names}

def agent_node(state: DynamicToolState) -> dict:
    """Invokes the LLM agent with the dynamically selected tools."""
    print("---AGENT: Deciding next action---")
    selected_names = state.get("selected_tool_names")
    if not selected_names:
        print("Error: No tools selected for the agent.")
        # Handle error - maybe respond directly or select default tools
        return {"messages": [AIMessage(content="I'm sorry, I encountered an issue selecting the right tools.")]}

    selected_tools = [TOOL_MAP[name] for name in selected_names]

    # Bind *only* the selected tools to the model for this invocation
    # model_with_selected_tools = model.bind_tools(selected_tools)
    print(f"Agent running with tools: {[t.name for t in selected_tools]}")

    # Placeholder: Simulate LLM call deciding to use a tool or respond
    last_message = state['messages'][-1]
    if "weather" in last_message.content.lower() and "get_weather" in selected_names:
         print("Agent decided to call get_weather.")
         # Simulate tool call generation - using ToolMessage directly for simplicity here
         # In reality, the AIMessage would contain tool_calls in its own format
         tool_call = ToolMessage(tool_call_id="tool_1", name="get_weather", content='{"location": "Paris"}')
         response = AIMessage(content="", tool_calls=[tool_call]) # Correctly format as AIMessage tool_calls
    elif "flight" in last_message.content.lower() and "get_flight_price" in selected_names:
         print("Agent decided to call get_flight_price.")
         tool_call = ToolMessage(tool_call_id="tool_2", name="get_flight_price", content='{"departure": "NYC", "arrival": "Tokyo"}')
         response = AIMessage(content="", tool_calls=[tool_call])
    else:
         print("Agent decided to respond directly.")
         response = AIMessage(content=f"I can help with that. Based on your query about '{last_message.content}', here's some information...")

    return {"messages": [response]}

def tool_node(state: DynamicToolState) -> dict:
    """Executes the tools called by the agent."""
    print("---TOOL EXECUTOR: Running tools---")
    last_message = state['messages'][-1]
    # Check if the last message is an AIMessage and has tool_calls
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        print("No tools called or last message is not an AIMessage with tool_calls.")
        return {}

    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name'] # Access name from the dict-like tool_call
        tool_to_call = TOOL_MAP.get(tool_name)
        if not tool_to_call:
            print(f"Error: Tool '{tool_name}' not found.")
            tool_messages.append(ToolMessage(content=f"Error: Tool '{tool_name}' not found.", tool_call_id=tool_call['id']))
            continue

        try:
            # Placeholder: Simulate tool execution
            args = tool_call['args'] # Access args from the dict-like tool_call
            result = tool_to_call.invoke(args)
            print(f"Tool '{tool_name}' executed successfully.")
            tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))
        except Exception as e:
            print(f"Error executing tool '{tool_name}': {e}")
            tool_messages.append(ToolMessage(content=f"Error executing tool: {e}", tool_call_id=tool_call['id']))

    return {"messages": tool_messages}


# --- Routing Function ---
def should_call_tools(state: DynamicToolState) -> Literal["tool_node", "__end__"]:
    """Decides whether to execute tools or end."""
    print("---ROUTER: Should call tools?---")
    last_message = state['messages'][-1]
    # Check if the last message is an AIMessage and has tool_calls
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print("Decision: Call tools.")
        return "tool_node"
    else:
        print("Decision: End.")
        return END

# --- Graph Definition ---
dynamic_tool_workflow = StateGraph(DynamicToolState)

dynamic_tool_workflow.add_node("select_tools", select_tools_node)
dynamic_tool_workflow.add_node("agent", agent_node)
dynamic_tool_workflow.add_node("tool_node", tool_node)

dynamic_tool_workflow.add_edge(START, "select_tools")
dynamic_tool_workflow.add_edge("select_tools", "agent")
dynamic_tool_workflow.add_conditional_edges(
    "agent",
    should_call_tools,
    {
        "tool_node": "tool_node",
        END: END
    }
)
dynamic_tool_workflow.add_edge("tool_node", "agent") # Loop back to agent after tools run

# --- Compile the Graph ---
dynamic_tool_agent = dynamic_tool_workflow.compile()

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     memory = MemorySaver()
#     config = {"configurable": {"thread_id": "dyn-tools-1"}}
#     initial_state = {
#         "messages": [HumanMessage(content="What's the weather like in Paris?")],
#     }
#     for event in dynamic_tool_agent.stream(initial_state, config=config):
#         print(event)
#         print("---")

#     print("\nStarting second query...")
#     config = {"configurable": {"thread_id": "dyn-tools-2"}}
#     initial_state_2 = {
#         "messages": [HumanMessage(content="How much is a flight from NYC to Tokyo?")],
#     }
#     for event in dynamic_tool_agent.stream(initial_state_2, config=config):
#         print(event)
#         print("---")