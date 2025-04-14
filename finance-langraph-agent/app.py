
import logging
import uuid
import asyncio # Import asyncio
from src.main import run_finance_query
from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()

async def main():
    """Runs the query and prints streamed results."""
    cli_thread_id = f"cli_thread_{uuid.uuid4()}"

    # query = "What is the current exchange rate for 1 USD to QAR?" # 3.65
    # query = "What is the current exchange rate for 1 GBP to QAR?" # 4.8747
    # query = "What is the current exchange rate for 1 EUR to QAR?"
    query = "What is 1 euro to qar"
    # query = "How much is 365 QAR in european currency?"
    # query = "How much is 1 GBP in QAR?"

    print(f"\n--- Running Query: '{query}' (Thread: {cli_thread_id}) ---")
    print("--- Agent Streamed Output ---")
    try:
        async for chunk in run_finance_query(query=query, thread_id=cli_thread_id):
            # Print each chunk as it arrives (tool calls, results, final answer)
            # Use end='' to avoid extra newlines between chunks if they don't have them
            print(chunk, end="", flush=True)
        print("\n---------------------------") # Add a final newline
    except Exception as e:
        logging.error(f"Error during CLI execution: {e}", exc_info=True)
        print(f"\n--- ERROR --- \n{e}\n-------------")

if __name__ == "__main__":
    asyncio.run(main())
