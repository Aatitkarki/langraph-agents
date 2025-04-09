from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END # START and END might not be needed if using set_entry_point/set_finish_point or tools_condition handles END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


@tool
def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    # The interrupt function pauses execution and waits for external input.
    # When resumed, it returns the value provided via Command(resume=...).
    # Here, we expect a dictionary with a "data" key.
    return human_response["data"]


tool = TavilySearchResults(max_results=2)
tools = [tool, human_assistance] # Added human_assistance tool
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Ensure only one tool call is made to avoid issues with interruption
    # This assertion might be too strict depending on the use case,
    # but it's included in the original tutorial code.
    assert(len(message.tool_calls) <= 1)
    return {"messages": [message]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools) # ToolNode now includes human_assistance
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    # The following dictionary maps the output of the conditional function to the next node
    # If the condition returns "tools", it goes to the "tools" node
    # If the condition returns "__end__", it ends the graph
    {"tools": "tools", "__end__": END} # Explicitly mapping __end__ to END
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot") # Setting the entry point

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Optional: Code to run the chatbot
# import getpass
# import os
# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")
# _set_env("ANTHROPIC_API_KEY")
# _set_env("TAVILY_API_KEY")

# user_input = "I need some expert guidance for building an AI agent. Could you request assistance for me?"
# config = {"configurable": {"thread_id": "1"}}

# events = graph.stream(
#     {"messages": [{"role": "user", "content": user_input}]},
#     config,
#     stream_mode="values",
# )
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()

# # Resume after interrupt
# human_response = (
#     "We, the experts are here to help! We'd recommend you check out LangGraph to build your agent."
#     " It's much more reliable and extensible than simple autonomous agents."
# )
# human_command = Command(resume={"data": human_response})

# events = graph.stream(human_command, config, stream_mode="values")
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()