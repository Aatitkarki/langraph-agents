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

def run_streamlit_messages(st_messages, callables,thread_id:str):
    logger.info("Invoking graph with messages: %s", st_messages)
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")

    config = RunnableConfig({"configurable": {"thread_id": thread_id},"callbacks":callables})

    result = finance_graph.invoke({"messages": st_messages}, config=config)
    logger.info("Graph invocation result: %s", result)
    return result

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