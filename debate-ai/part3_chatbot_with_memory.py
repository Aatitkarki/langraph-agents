from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END # START and END might not be needed if using set_entry_point/set_finish_point or tools_condition handles END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition # tools_condition is used in the graph definition


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


tool = TavilySearchResults(max_results=2)
tools = [tool]
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    # The following dictionary maps the output of the conditional function to the next node
    # If the condition returns "tools", it goes to the "tools" node
    # If the condition returns "__end__", it ends the graph
    {"tools": "tools", "__end__": END} # Explicitly mapping __end__ to END
)
# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot") # Setting the entry point

# Add the checkpointer
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

# config = {"configurable": {"thread_id": "1"}}
# user_input = "Hi there! My name is Will."
# events = graph.stream(
#     {"messages": [{"role": "user", "content": user_input}]},
#     config,
#     stream_mode="values",
# )
# for event in events:
#     event["messages"][-1].pretty_print()

# user_input = "Remember my name?"
# events = graph.stream(
#     {"messages": [{"role": "user", "content": user_input}]},
#     config,
#     stream_mode="values",
# )
# for event in events:
#     event["messages"][-1].pretty_print()