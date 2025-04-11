import streamlit as st
from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Import constants - assumes constants.py and .env are set up
try:
    from constants import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL_NAME,LANGFUSE_HANDLER
except ImportError:
    st.error("Could not import constants. Make sure constants.py and .env are set up correctly.")
    st.stop()

# --- LangGraph State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- LangGraph Definition ---
def build_graph():
    """Builds the LangGraph graph."""
    graph_builder = StateGraph(State)

    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE, # Will be None if not set in constants/env
        model=OPENAI_MODEL_NAME
    )

    def chatbot_node(state: State):
        print("---LLM INVOKED (Streamlit)---") # For server logs
        # The state["messages"] already contains BaseMessage objects (HumanMessage, AIMessage)
        # due to the add_messages annotation. Directly pass it to the LLM.
        response = llm.invoke(state["messages"])
        # Return in the format expected by add_messages
        return {"messages": [response]}

    graph_builder.add_node("chatbot", chatbot_node)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)

    # Compile the graph (no checkpointer needed for this basic version unless memory is desired)
    graph = graph_builder.compile().with_config({"callbacks": [LANGFUSE_HANDLER]})
    return graph

# --- Streamlit App ---

st.set_page_config(page_title="Basic LangGraph Chatbot", layout="wide")
st.title("💬 Basic LangGraph Chatbot")
st.caption("🚀 A simple chatbot powered by LangGraph and OpenAI.")

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "graph" not in st.session_state:
    # Build and store the graph in session state to avoid recompiling on each interaction
    st.session_state.graph = build_graph()

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input field
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to session state and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare graph input from session state messages
    graph_input_messages = [
        HumanMessage(content=m["content"]) if m["role"] == "user"
        else AIMessage(content=m["content"])
        for m in st.session_state.messages
    ]
    graph_input = {"messages": graph_input_messages}

    # Define config (using a fixed thread_id for simplicity in this basic example)
    # For persistent memory across sessions, a checkpointer would be needed here
    # and potentially a unique thread_id per user/session.
    config = {"configurable": {"thread_id": "streamlit-basic-chat-1"}}

    # Invoke the graph and display response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Use stream for potential future streaming LLMs, though basic invoke works too
            # stream_mode="values" gives the full state dict
            events = st.session_state.graph.stream(
                graph_input,
                config=config,
                stream_mode="values"
            )

            for event in events:
                # The basic graph has only one step, so we expect one event with the final state
                if "messages" in event:
                    ai_message = event["messages"][-1]
                    if isinstance(ai_message, AIMessage):
                        full_response = ai_message.content
                        message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)
            if full_response:
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"An error occurred: {e}")
            # Optionally remove the last user message if processing failed
            # st.session_state.messages.pop()