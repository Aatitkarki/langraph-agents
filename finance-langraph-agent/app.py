from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from st_callable_util import get_streamlit_cb  # Utility function to get a Streamlit callback handler with context

import logging
import streamlit as st
import uuid

# Import the core agent execution function and API key constant from the new structure
from src.main import run_streamlit_messages
from src.utils.logging_config import setup_logging # API Key loaded from env vars

load_dotenv()
# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰")

setup_logging(level=logging.DEBUG)

# --- Main Chat Interface ---
st.title("💰 Banking Agent Chatbot")
st.caption("🚀 Ask me about your accounts, transactions, cards, or exchange rates!")

# Initialize the expander state
if "expander_open" not in st.session_state:
    st.session_state.expander_open = True

# Capture user input from chat input
prompt = st.chat_input()

# Toggle expander state based on user input
if prompt is not None:
    st.session_state.expander_open = False  # Close the expander when the user starts typing

# st write magic
with st.expander(label="Ask questions regarding your finance data", expanded=st.session_state.expander_open):
    """
    Banking agent chatbot can help to ease your banking experience.
    """

# Initialize chat messages in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content="How can I help you?")]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content="How can I help you today?")]
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = f"streamlit_thread_{uuid.uuid4()}" # Unique thread ID per session

# Loop through all messages in the session state and render them as a chat on every st.refresh mech
for msg in st.session_state.messages:
    # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
    if isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("random").write(msg.content)

# Handle user input if provided
if prompt:
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        # create a new placeholder for streaming messages and other events, and give it context
        st_callback = get_streamlit_cb(st.container())
        response = run_streamlit_messages(st.session_state.messages, [st_callback],thread_id=st.session_state.thread_id)
        st.session_state.messages.append(AIMessage(content=response["messages"][-1].content))   # Add that last message to the st_message_state


# # Display chat messages from history on app rerun
# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# # Accept user input
# if prompt := st.chat_input("What would you like to ask?"):
#     # Check for API key before proceeding
#     if not st.session_state.openai_api_key:
#         st.info("Please add your OpenAI API key in the sidebar to continue.")
#         st.stop()

#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     # Display user message in chat message container
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # Display thinking indicator
#     # with st.chat_message("assistant"):
#     with st.spinner("Thinking..."):
#         # Call the banking agent function
#         try:
#             response = run_single_query(
#                 query=prompt,
#                 thread_id=st.session_state.thread_id,
#                 openai_api_key=st.session_state.openai_api_key # Pass the key
#             )
#             msg_content = response
#         except Exception as e:
#             st.error(f"An error occurred: {e}")
#             msg_content = "Sorry, I encountered an error. Please try again."

#         # Display assistant response
#     with st.chat_message("assistant"):
#         st.markdown(msg_content)
#     st.session_state.messages.append({"role": "assistant", "content": msg_content})
