TAVILY_API_KEY="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"
import asyncio
import json
import logging
import uuid
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

# Local utilities and project modules
from src.graph.builder import finance_graph
from src.utils.logging_config import setup_logging

# --- Configuration and Logging ---
load_dotenv()
setup_logging(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --- Core Agent Streaming Logic ---

async def stream_streamlit_messages(st_messages, output_container, thread_id: str) -> str:
    """
    Runs messages through the finance graph, streaming events to Streamlit placeholders.

    Args:
        st_messages: List of messages (HumanMessage, AIMessage) from Streamlit session state.
        output_container: The Streamlit container where dynamic UI elements will be placed.
        thread_id: The unique identifier for the current conversation thread.

    Returns:
        The final accumulated text response from the agent stream.
    """
    logger.info("Streaming graph with %d messages for thread: %s", len(st_messages), thread_id)

    thoughts_placeholder = output_container.container()  # Container for tool status messages
    token_placeholder = output_container.empty()  # Placeholder for the streaming response text
    final_text = ""
    output_placeholder = None # Initialize placeholder for tool output

    config = RunnableConfig({"configurable": {"thread_id": thread_id}})

    try:
        logger.info("--- [stream_streamlit_messages] Starting astream_events... ---")
        async for event in finance_graph.astream_events(
            {"messages": st_messages}, config=config, version="v2"
        ):
            kind = event["event"]
            logger.debug(f"Event received: {kind}")

            if kind == "on_chat_model_stream":
                # Safely access chunk content
                chunk = event["data"].get("chunk")
                # Ensure chunk exists and has content before accessing
                addition = chunk.content if chunk is not None and hasattr(chunk, 'content') else None
                if addition:
                    final_text += addition
                    token_placeholder.write(final_text) # Update progressive response

            elif kind == "on_tool_start":
                logger.debug(f"Tool Event Started: {event['name']}")
                with thoughts_placeholder:
                    # Use status widget for better UX
                    with st.status(f"Calling Tool: `{event['name']}`...", expanded=True) as status:
                        st.write("Input:")
                        st.code(event['data'].get('input'), language='json') # Assume input is dict-like
                        output_placeholder = st.empty() # Create placeholder for output *inside* status
                        # Status will be updated in on_tool_end

            elif kind == "on_tool_end":
                logger.debug(f"Tool Event Ended: {event['name']}")
                tool_output = event['data'].get('output') # Safely get potential output
                # Find the corresponding status widget to update it
                # Note: This relies on Streamlit's execution model. If complex, might need explicit state management.
                if output_placeholder: # Check if the placeholder was created
                    # Check if tool_output exists before accessing attributes or converting
                    if tool_output is not None:
                        output_content = tool_output.content if hasattr(tool_output, 'content') else str(tool_output)
                    else:
                        output_content = "[No output data]" # Or handle as appropriate
                    output_placeholder.code(output_content, language='text') # Display tool output
                    # Update the status label - assumes status is still accessible; might need refinement
                    # This part is tricky with async/streamlit; might need explicit status handle storage if issues arise.
                    # For now, let's assume the context works. If not, remove the status update logic.
                    # status.update(label=f"Tool `{event['name']}` Finished", state="complete", expanded=False) # Requires status handle

        logger.info("--- [stream_streamlit_messages] Streaming finished. ---")
        return final_text

    except Exception as e:
        logger.error("--- [stream_streamlit_messages] ERROR during graph streaming: %s ---", e, exc_info=True)
        error_message = f"An error occurred during processing: {e}"
        token_placeholder.error(error_message) # Display error in the chat UI
        return error_message # Return error message to be handled upstream

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰", layout="wide")
logger.info("Streamlit page configured.")

# --- Helper Functions ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [AIMessage(content="How can I help you?")]
        logger.debug("Initialized chat messages in session state.")
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = f"streamlit_thread_{uuid.uuid4()}"
        logger.debug(f"Initialized thread ID: {st.session_state['thread_id']}")
    if "expander_open" not in st.session_state:
         st.session_state.expander_open = True # Default expander state

def display_messages():
    """Displays chat messages from session state."""
    for msg in st.session_state.messages:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        with st.chat_message(role):
            st.write(msg.content)

def process_response(response_str: str):
    """Parses the agent response, extracting message content if JSON is found within the string."""
    stripped_response = response_str.strip() if response_str else ""
    final_content = stripped_response # Default to the stripped raw response

    if not stripped_response:
        logger.warning("Received empty response string.")
        return ""

    # Try to find the JSON part within the string
    json_start = stripped_response.find('{')
    json_end = stripped_response.rfind('}')

    # Ensure '{' comes before '}' and both are found
    if json_start != -1 and json_end != -1 and json_start < json_end:
        potential_json_str = stripped_response[json_start : json_end + 1]
        logger.debug(f"Attempting to parse potential JSON substring: '{potential_json_str}'")
        try:
            response_json = json.loads(potential_json_str)
            if isinstance(response_json, dict) and 'message' in response_json:
                # Successfully parsed and found the message key
                final_content = response_json['message']
                logger.info(f"Extracted message from JSON substring: {final_content}")
                return final_content # Return successfully extracted message
            else:
                logger.warning(f"Parsed JSON substring but lacked 'message' key or wasn't a dict: {potential_json_str}")
                # Fall through to return original stripped response
        except json.JSONDecodeError as json_err:
            # Log the specific JSON error and the problematic substring
            logger.warning(f"JSONDecodeError on substring: {json_err}. String was: '{potential_json_str}'")
            # Fall through to return the original stripped response if substring parsing fails
        except Exception as e:
            logger.error(f"Unexpected error processing JSON substring '{potential_json_str[:100]}...': {e}", exc_info=True)
            # Fall through to return original stripped response
    else:
        # Log if JSON markers weren't found properly
        logger.info(f"No valid JSON object markers '{{...}}' found in response, using raw string: '{stripped_response}'")

    # If JSON parsing failed or wasn't attempted, return the original stripped string
    logger.info(f"Returning raw/stripped response: '{final_content}'")
    return final_content

# --- Main Chat Interface ---
st.title("💰 Banking Agent Chatbot")
st.caption("🚀 Ask me about your accounts, transactions, cards, or exchange rates!")

# Initialize session state if needed
initialize_session_state()

# Display introductory text in an expander
with st.expander(label="Ask questions regarding your finance data", expanded=st.session_state.expander_open):
    st.write("Banking agent chatbot can help to ease your banking experience.")

# Display existing chat messages
display_messages()

# Handle user input
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.expander_open = False # Close expander on input
    st.session_state.messages.append(HumanMessage(content=prompt))
    st.chat_message("user").write(prompt)
    logger.info(f"User prompt: {prompt[:50]}...")

    # Display assistant response placeholder and stream agent output
    with st.chat_message("assistant"):
        st_container = st.container() # Container for streaming output and tool status
        logger.info(f"Calling stream_streamlit_messages for thread_id: {st.session_state.thread_id}")

        # Run the async streaming function
        response_string = asyncio.run(
            stream_streamlit_messages(
                st.session_state.messages,
                output_container=st_container,
                thread_id=st.session_state.thread_id
            )
        )

        # Process the final response string (potentially JSON)
        final_message_content = process_response(response_string)

        # Add the final message to session state, handling potential errors
        if final_message_content: # Avoid adding empty messages if processing failed badly
            try:
                last_message = AIMessage(content=final_message_content)
                st.session_state.messages.append(last_message)
                logger.info("Added final AIMessage to session state.")
            except Exception as e:
                logger.error(f"Error adding final AIMessage to session state: {e}", exc_info=True)
                # Display error in UI if adding failed
                st_container.error(f"Sorry, encountered an error finalizing the response: {e}")
        else:
             logger.warning("Final message content was empty after processing, not adding to history.")

        # Rerun to clear the temporary streaming placeholders if needed,
        # though Streamlit often handles this well. Explicit rerun can ensure clean state.
        # st.rerun() # Uncomment if placeholders sometimes linger
