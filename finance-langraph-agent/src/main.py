
import traceback
import asyncio # Add asyncio
from typing import Optional, AsyncIterator # Add AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

# Import the compiled graph
from src.graph.builder import finance_graph

# Note: LLM configuration (including API key handling) is now in src.utils.llm_config
# The Streamlit app will handle passing the key if provided via UI.

# Change to async def and yield strings
async def run_finance_query(query: str, thread_id: str, openai_api_key: Optional[str] = None) -> AsyncIterator[str]:
    """Runs a query through the finance graph and streams back intermediate steps and the final response."""
    print(f"\n--- [run_finance_query - STREAMING] START ---")
    print(f"Query: '{query}'")
    print(f"Thread ID: {thread_id}")
    print(f"API Key Provided: {'Yes' if openai_api_key else 'No'}") # Don't print the key
    # Configuration for the graph invocation, using the provided thread_id
    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    final_answer = ""

    print(f"--- [run_finance_query - STREAMING] Streaming finance_graph events... ---")
    try:
        # Use astream_events V2
        async for event in finance_graph.astream_events(
            {"messages": [HumanMessage(content=query)]},
            config=config,
            version="v2" # Use v2 for more structured events
        ):
            kind = event["event"]
            name = event.get("name", "") # Node name
            tags = event.get("tags", []) # Tags like 'tool_call', 'llm'
            # print(f"Event: {kind}, Name: {name}, Tags: {tags}, Data: {event['data']}") # Debug print

            if kind == "on_tool_start":
                tool_input = event["data"].get("input", {})
                yield f"🛠️ **Calling Tool:** `{name}` with input: `{tool_input}`"
            elif kind == "on_tool_end":
                tool_output = event["data"].get("output", "")
                # Shorten potentially long outputs for display
                output_display = str(tool_output)
                if len(output_display) > 200:
                    output_display = output_display[:200] + "..."
                yield f"✅ **Tool Result:** `{name}` returned: `{output_display}`"
            elif kind == "on_chat_model_stream":
                 # Stream intermediate LLM thoughts/tokens if needed (can be verbose)
                 # chunk_content = event["data"].get("chunk", {}).get("content", "")
                 # if chunk_content:
                 #     yield chunk_content # Stream partial LLM responses
                 pass # Keep it less verbose for now, focus on tools
            elif kind == "on_chain_end" and name == "FinanceGraph": # Check for the end of the main graph
                # The final answer is usually in the output of the graph end event
                final_output_messages = event["data"].get("output", {}).get("messages", [])
                if final_output_messages:
                    last_msg = final_output_messages[-1]
                    if hasattr(last_msg, 'content'):
                        final_answer = last_msg.content
                    else:
                        final_answer = str(last_msg)
                    print(f"--- [run_finance_query - STREAMING] Final Answer detected: {final_answer} ---")
                else:
                     print(f"--- [run_finance_query - STREAMING] No messages found in final graph output. ---")
                     final_answer = "Agent finished but provided no final message."


        # Yield the final answer after the stream is done
        if final_answer:
             yield f"\n---\n**Final Answer:**\n{final_answer}"
        else:
             yield "Agent execution finished, but no final answer was extracted."


    except Exception as e:
        print(f"--- [run_finance_query - STREAMING] ERROR during graph streaming: {e} ---")
        traceback.print_exc()
        yield f"An error occurred during execution: {e}"
    finally:
        print(f"--- [run_finance_query - STREAMING] END ---")

# Example queries are removed as this file is meant to be imported as a module.
# Testing should be done via the Streamlit app or separate test scripts.