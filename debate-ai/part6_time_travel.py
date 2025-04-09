from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END # START and END might not be needed if using set_entry_point/set_finish_point or tools_condition handles END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


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

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Optional: Code to run the chatbot and demonstrate time travel
# import getpass
# import os
# def _set_env(var: str):
#     if not os.environ.get(var):
#         os.environ[var] = getpass.getpass(f"{var}: ")
# _set_env("ANTHROPIC_API_KEY")
# _set_env("TAVILY_API_KEY")

# config = {"configurable": {"thread_id": "1"}}
# events = graph.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": (
#                     "I'm learning LangGraph. "
#                     "Could you do some research on it for me?"
#                 ),
#             },
#         ],
#     },
#     config,
#     stream_mode="values",
# )
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()

# events = graph.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": (
#                     "Ya that's helpful. Maybe I'll "
#                     "build an autonomous agent with it!"
#                 ),
#             },
#         ],
#     },
#     config,
#     stream_mode="values",
# )
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()

# # Replay history and select a state to resume from
# to_replay = None
# for state in graph.get_state_history(config):
#     print("Num Messages: ", len(state.values["messages"]), "Next: ", state.next)
#     print("-" * 80)
#     if len(state.values["messages"]) == 6: # Arbitrarily selecting a state
#         to_replay = state

# if to_replay:
#     print("\nResuming from selected state:")
#     print(to_replay.next)
#     print(to_replay.config)
#     # Resume execution from the selected checkpoint
#     for event in graph.stream(None, to_replay.config, stream_mode="values"):
#         if "messages" in event:
#             event["messages"][-1].pretty_print()