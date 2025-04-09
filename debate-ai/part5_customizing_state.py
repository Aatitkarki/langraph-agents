from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END # START and END might not be needed if using set_entry_point/set_finish_point or tools_condition handles END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt


# Define the state with custom keys 'name' and 'birthday'
class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str


graph_builder = StateGraph(State)


@tool
def human_assistance(
    name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command: # Changed return type hint to Command
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )
    # If the information is correct, update the state as-is.
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    # Otherwise, receive information from the human reviewer.
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside
    # the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)


tool = TavilySearchResults(max_results=2)
tools = [tool, human_assistance] # Added human_assistance tool
llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Ensure only one tool call is made to avoid issues with interruption
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

# user_input = (
#     "Can you look up when LangGraph was released? "
#     "When you have the answer, use the human_assistance tool for review."
# )
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
# human_command = Command(
#     resume={
#         "name": "LangGraph",
#         "birthday": "Jan 17, 2024",
#     },
# )

# events = graph.stream(human_command, config, stream_mode="values")
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()

# # Check state
# snapshot = graph.get_state(config)
# print({k: v for k, v in snapshot.values.items() if k in ("name", "birthday")})

# # Update state manually
# graph.update_state(config, {"name": "LangGraph (library)"})
# snapshot = graph.get_state(config)
# print({k: v for k, v in snapshot.values.items() if k in ("name", "birthday")})