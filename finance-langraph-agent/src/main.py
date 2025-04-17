import logging
import traceback
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

# Import the compiled graph
from src.graph.builder import finance_graph

# Note: LLM configuration (including API key handling) is now in src.utils.llm_config
# The Streamlit app will handle passing the key if provided via UI.

logger = logging.getLogger(__name__)

async def run_streamlit_messages(st_messages, callables, thread_id: str): # Changed to async def
    """Runs messages through the graph using streaming events."""
    logger.info("Streaming graph with messages: %s for thread: %s", st_messages, thread_id)
    if not isinstance(callables, list):
        # Assuming callables might be used for UI updates, ensure it's usable
        logger.warning("Callbacks provided are not a list, UI updates might fail.")
        # Decide how to handle this - raise error or proceed without callbacks?
        # For now, let's proceed but log warning.
        # raise TypeError("callables must be a list")

    config = RunnableConfig({"configurable": {"thread_id": thread_id}, "callbacks": callables})
    final_response_content = "" # Optional: Accumulate final response if needed

    try:
        logger.info("--- [run_streamlit_messages] Starting astream_events... ---")
        async for event in finance_graph.astream_events(
            {"messages": st_messages}, config=config, version="v1" # Specify event version
        ):
            kind = event["event"]
            # logger.debug(f"Stream Event: {kind}, Data: {event['data']}") # Verbose logging

            # --- Handle specific event types for Streamlit ---
            # This logic needs to be tightly coupled with how the Streamlit app
            # expects to receive updates (likely via the 'callables').

            if kind == "on_chat_model_stream":
                # Safely access chunk content
                data = event.get("data", {})
                chunk = data.get("chunk")
                content = getattr(chunk, 'content', None) if chunk else None

                if content:
                    # TODO: Integrate with Streamlit callback/handler in `callables`
                    # e.g., callables[0].append_token(content)
                    logger.debug(f"LLM Stream Chunk: {content}")
                    final_response_content += content # Example accumulation

            elif kind == "on_tool_start":
                tool_name = event["data"].get("name", "Unknown Tool")
                logger.info(f"Tool Started: {tool_name}")
                # TODO: Integrate with Streamlit status update callback
                # e.g., callables[0].update_status(f"Running tool: {tool_name}...")

            elif kind == "on_tool_end":
                tool_name = event["data"].get("name", "Unknown Tool")
                output = event["data"].get("output", "") # Get tool output if available
                logger.info(f"Tool Ended: {tool_name}")
                # logger.debug(f"Tool Output: {output}") # Optional: log tool output
                # TODO: Integrate with Streamlit status update callback
                # e.g., callables[0].update_status(f"Tool {tool_name} finished.")

            # Add more event handlers (on_node_start, on_node_end, etc.) if needed for UI feedback

        logger.info("--- [run_streamlit_messages] Streaming finished. ---")

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

def run_single_query(query: str, thread_id: str, openai_api_key: Optional[str] = None): # Key is passed but not directly used here; llm instance uses env/initial config
    """Runs a query through the finance graph and returns the final response string."""
    logger.info("--- [run_single_query] START ---")
    logger.info("Query: '%s'", query)
    logger.info("Thread ID: %s", thread_id)
    logger.info("API Key Provided: %s", 'Yes' if openai_api_key else 'No') # Don't print the key

    # Configuration for the graph invocation, using the provided thread_id
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    final_state = None
    logger.info("--- [run_single_query] Invoking finance_graph... ---")
    try:
        # Invoke the graph with the user query
        final_state = finance_graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        logger.info("--- [run_single_query] Invocation finished. ---")
        # logger.debug("Final State: %s", final_state) # Optional: Log the whole state for debugging
    except Exception as e:
        logger.error("--- [run_single_query] ERROR during graph invocation: %s ---", e)
        logger.exception("Exception during graph invocation:") # Log full traceback
        return f"Error during agent execution: {e}"

    # Process final response from the state
    if final_state and isinstance(final_state, dict) and final_state.get('messages'):
        try:
            # Get the last message, which should be the final response
            last_msg = final_state['messages'][-1]
            logger.debug("--- [run_single_query] Last message object: %s ---", last_msg)

            # Extract content based on message type
            if isinstance(last_msg, AIMessage):
                response_content = last_msg.content
            elif isinstance(last_msg, HumanMessage):
                 # If the last message was the formatted one from a worker node or supervisor summary
                 response_content = last_msg.content
            elif isinstance(last_msg, ToolMessage):
                 response_content = f"Tool execution result: {last_msg.content}" # Less ideal, supervisor should summarize
            elif hasattr(last_msg, 'content'):
                 response_content = last_msg.content # General fallback
            else:
                 response_content = str(last_msg) # Raw fallback

            logger.info("--- [run_single_query] Extracted response: %s ---", response_content)
            logger.info("--- [run_single_query] END ---")
            return response_content
        except Exception as e:
            logger.error("--- [run_single_query] ERROR processing final state: %s ---", e)
            return f"Error processing agent response: {e}"
    else:
        logger.warning("--- [run_single_query] No final state or messages found. ---")
        logger.info("--- [run_single_query] END ---")
        return "Agent did not produce a final response."

# Example queries are removed as this file is meant to be imported as a module.
# Testing should be done via the Streamlit app or separate test scripts.