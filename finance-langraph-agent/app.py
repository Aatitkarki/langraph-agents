
import logging
import uuid

from src.main import run_finance_query
from src.utils.logging_config import setup_logging

    # Generate a unique thread ID for this CLI run
# Configure logging
setup_logging()

cli_thread_id = f"cli_thread_{uuid.uuid4()}"

# query = "What is the current exchange rate for 1 USD to QAR?" # 3.65
# query = "What is the current exchange rate for 1 GBP to QAR?" # 4.8747
# query = "What is the current exchange rate for 1 EUR to QAR?" 
query = "How much is 365 QAR in european currency?" 
# query = "How much is 1 GBP in QAR?" 


final_response = run_finance_query(query=query, thread_id=cli_thread_id)

print("\n--- Agent Final Response ---")
print(final_response)
print("---------------------------")
