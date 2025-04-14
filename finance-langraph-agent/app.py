
import uuid

from src.main import run_finance_query

    # Generate a unique thread ID for this CLI run
cli_thread_id = f"cli_thread_{uuid.uuid4()}"

query = "What is the current exchange rate for USD to EUR?"

final_response = run_finance_query(query=query, thread_id=cli_thread_id)

print("\n--- Agent Final Response ---")
print(final_response)
print("---------------------------")
