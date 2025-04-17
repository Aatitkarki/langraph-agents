import asyncio
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from st_callable_util import get_streamlit_cb  # Utility function to get a Streamlit callback handler with context

import logging
import streamlit as st
import uuid

# Import the core agent execution function and API key constant from the new structure
from src.main import run_streamlit_messages # Removed stream_streamlit_messages as it's defined locally
from src.graph.builder import finance_graph
from src.utils.logging_config import setup_logging # API Key loaded from env vars

load_dotenv()
setup_logging(level=logging.DEBUG)

logger = logging.getLogger(__name__)

async def stream_streamlit_messages(st_messages, st_placeholder , thread_id: str) -> str:
    """Runs messages through the graph using streaming events."""
    logger.info("Streaming graph with messages: %s for thread: %s", st_messages, thread_id)

    container = st_placeholder  # This container will hold the dynamic Streamlit UI components
    thoughts_placeholder = container.container()  # Container for displaying status messages
    token_placeholder = container.empty()  # Placeholder for displaying progressive token updates
    final_text = "" 

    config = RunnableConfig({"configurable": {"thread_id": thread_id}})

    try:
        logger.info("--- [run_streamlit_messages] Starting astream_events... ---")
        async for event in finance_graph.astream_events(
            {"messages": st_messages}, config=config, version="v2" # Specify event version
        ):
            kind = event["event"]

            # --- Handle specific event types for Streamlit ---
            # This logic needs to be tightly coupled with how the Streamlit app
            # expects to receive updates (likely via the 'callables').

            if kind == "on_chat_model_stream":
                logger.debug(f"The event kind is {kind}")
                # The event corresponding to a stream of new content (tokens or chunks of text)
                addition = event["data"]["chunk"].content  # type: ignore # Extract the new content chunk
                final_text += addition  # Append the new content to the accumulated text
                if addition:
                    token_placeholder.write(final_text)  # Update the st placeholder with the progressive response

            elif kind == "on_tool_start":
                logger.debug(f"Tool Event Started : {event}") # Verbose logging
                # The event signals that a tool is about to be called
                with thoughts_placeholder:
                    status_placeholder = st.empty()  # Placeholder to show the tool's status
                    with status_placeholder.status("Calling Tool...", expanded=True) as s:
                        st.write("Called ", event['name'])  # Show which tool is being called
                        st.write("Tool input: ")
                        st.code(event['data'].get('input'))  # Display the input data sent to the tool
                        st.write("Tool output: ")
                        output_placeholder = st.empty()  # Placeholder for tool output that will be updated later below
                        s.update(label="Completed Calling Tool!", expanded=False)  # Update the status once done

            elif kind == "on_tool_end":
                logger.debug(f"Tool Event Ended : {event}") # Verbose logging
                # The event signals that a tool is about to be called
                # The event signals the completion of a tool's execution
                with thoughts_placeholder:
                    # We assume that `on_tool_end` comes after `on_tool_start`, meaning output_placeholder exists
                    if 'output_placeholder' in locals():
                        output_placeholder.code(event['data'].get('output').content)  # type: ignore # Display the tool's output

                # Add more event handlers (on_node_start, on_node_end, etc.) if needed for UI feedback

        logger.info("--- [run_streamlit_messages] Streaming finished. ---")
        return final_text;

    except Exception as e:
        logger.error("--- [run_streamlit_messages] ERROR during graph streaming: %s ---", e)
        logger.exception("Exception during graph streaming:")
        # TODO: Integrate with Streamlit error display callback
        # e.g., callables[0].display_error(f"Error: {e}")
        # Depending on Streamlit app structure, might need to return error status
        raise # Re-raise for potential higher-level handling

    # Return value might be less relevant if UI is updated directly via callbacks
    # Return None or status, or accumulated content if needed elsewhere
    return None # Modified: Return None as updates happen via stream/callbacks


# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰")
logger.info("Streamlit page configured.")


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
    logger.debug("Initializing chat messages in session state.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [AIMessage(content="How can I help you today?")]
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = f"streamlit_thread_{uuid.uuid4()}" # Unique thread ID per session
    logger.debug(f"Initializing thread ID in session state: {st.session_state['thread_id']}")

# Loop through all messages in the session state and render them as a chat on every st.refresh mech
for msg in st.session_state.messages:
    logger.debug(f"Rendering message of type: {type(msg).__name__}")
    # we store them as AIMessage and HumanMessage as its easier to send to LangGraph
    if isinstance(msg, AIMessage):
        st.chat_message("assistant").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("random").write(msg.content)

# Handle user input if provided
if prompt:
    logger.info(f"Received user prompt: {prompt[:50]}...") # Log first 50 chars
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        # create a new placeholder for streaming messages and other events, and give it context
        st_container = st.container()
        logger.info(f"Calling run_streamlit_messages for thread_id: {st.session_state.thread_id}")
        response = asyncio.run(stream_streamlit_messages(st.session_state.messages,st_placeholder=st_container ,thread_id=st.session_state.thread_id))
        # last_message = response["messages"][-1]
        last_message = AIMessage(response);
        logging.debug(f"Response from run_streamlit_messages: {last_message.content}")
        current_session_message = st.session_state.messages
        logging.debug(f"Current session message: {current_session_message}")
        try:
            logging.debug(f"Adding AIMessage to session state:")
            st.session_state.messages.append(last_message)   # Add that last message to the st_message_state
            logging.debug(f"Added the AIMessage to session state: {last_message.content}")
        except Exception as e:
            logger.error(f"Error adding AIMessage to session state: {e}")
            st.session_state.messages.append(AIMessage(content="Sorry, I encountered an error. Please try again."))
        logger.info(f"Received response from run_streamlit_messages. Adding AIMessage to state.")


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
