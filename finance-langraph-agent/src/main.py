import traceback
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

# Import the compiled graph
from src.graph.builder import finance_graph

# Note: LLM configuration (including API key handling) is now in src.utils.llm_config
# The Streamlit app will handle passing the key if provided via UI.

def run_streamlit_messages(st_messages, callables,thread_id:str):
    print("Invoking graph",st_messages)
    if not isinstance(callables, list):
        raise TypeError("callables must be a list")

    config = RunnableConfig({"configurable": {"thread_id": thread_id},"callbacks":callables})

    return finance_graph.invoke({"messages": st_messages}, config=config)

def run_single_query(query: str, thread_id: str, openai_api_key: Optional[str] = None): # Key is passed but not directly used here; llm instance uses env/initial config
    """Runs a query through the finance graph and returns the final response string."""
    print(f"\n--- [run_finance_query] START ---")
    print(f"Query: '{query}'")
    print(f"Thread ID: {thread_id}")
    print(f"API Key Provided to run_finance_query: {'Yes' if openai_api_key else 'No'}") # Don't print the key

    # Configuration for the graph invocation, using the provided thread_id
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    final_state = None
    print(f"--- [run_finance_query] Invoking finance_graph... ---")
    try:
        # Invoke the graph with the user query
        final_state = finance_graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        print(f"--- [run_finance_query] Invocation finished. ---")
        # print(f"Final State: {final_state}") # Optional: Print the whole state for debugging
    except Exception as e:
        print(f"--- [run_finance_query] ERROR during graph invocation: {e} ---")
        traceback.print_exc() # Print full traceback
        return f"Error during agent execution: {e}"

    # Process final response from the state
    if final_state and isinstance(final_state, dict) and final_state.get('messages'):
        try:
            # Get the last message, which should be the final response
            last_msg = final_state['messages'][-1]
            print(f"--- [run_finance_query] Last message object: {last_msg} ---")

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

            print(f"--- [run_finance_query] Extracted response: {response_content} ---")
            print(f"--- [run_finance_query] END ---")
            return response_content
        except Exception as e:
            print(f"--- [run_finance_query] ERROR processing final state: {e} ---")
            return f"Error processing agent response: {e}"
    else:
        print(f"--- [run_finance_query] No final state or messages found. ---")
        print(f"--- [run_finance_query] END ---")
        return "Agent did not produce a final response."

# Example queries are removed as this file is meant to be imported as a module.
# Testing should be done via the Streamlit app or separate test scripts.