import logging
from typing import Annotated, List, Optional, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import transactions_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_transactions(account_number: Annotated[Optional[str], "Optional account number to filter transactions."],
                     limit: Annotated[Optional[int], "Optional limit on the number of transactions to return."]) -> List[Dict]:
    """
    Retrieves the transaction history for the user's account.
    Optionally filters by account number (mock ignores this) and limits the number of results.
    """
    logger.info(f"Tool: get_transactions called (Account: {account_number}, Limit: {limit})")
    # Access the pre-loaded mock data
    data = transactions_data.get("ResponseData", [])
    if not data:
         error_msg = "No transaction data available."
         logger.error(f"Error in get_transactions: {error_msg}")
         return [{"Error": error_msg}]
    if limit:
        return data[:limit]
    return data