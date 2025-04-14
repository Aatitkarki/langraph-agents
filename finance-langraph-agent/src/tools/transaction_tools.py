import logging
from typing import Annotated, List, Optional, Dict
from langchain_core.tools import tool

# Import the transaction data loaded in data_loader
from src.utils.data_loader import transactions_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_transactions(
    account_number: Annotated[Optional[str], "Optional account number to filter transactions. NOTE: This is currently ignored by the pre-loaded data source."] = None,
    limit: Annotated[Optional[int], "Optional limit on the number of transactions to return."] = None
) -> List[Dict]:
    """
    Fetches the transaction history for the user from pre-loaded JSON data.

    This tool retrieves a list of transactions. It can optionally limit the number
    of transactions returned. The account_number filter is accepted but currently
    ignored by the underlying pre-loaded data source, which returns all transactions.

    Args:
        account_number: An optional account number string. (Currently ignored).
        limit: An optional integer to limit the number of transactions returned.
               If omitted, all available transactions are returned.

    Returns:
        A list of dictionaries, where each dictionary represents a transaction.
        - On success: Each dictionary includes fields like TransactionDate, Description,
          Amount, Currency, RunningBalance, etc.
          Example subset: {'TransactionDate': '2024-07-15T10:30:00', 'Description': 'Grocery Store Purchase', 'Amount': -55.75}
        - If no transaction data is found: Returns a list containing a single dictionary with an error message.
          Example: [{'Error': 'No transaction data available.'}]
    """
    logger.info(f"Tool: get_transactions called (Account: {account_number}, Limit: {limit})")
    # Access the pre-loaded JSON data
    all_transactions = transactions_data.get("ResponseData", [])
    if not all_transactions:
         error_msg = "No transaction data available."
         logger.error(f"Error in get_transactions: {error_msg}")
         return [{"Error": error_msg}]

    # Apply limit if provided
    if limit is not None and limit > 0:
        result_transactions = all_transactions[:limit]
        logger.info(f"Tool: get_transactions returning {len(result_transactions)} transaction(s) (limited)")
    else:
        result_transactions = all_transactions
        logger.info(f"Tool: get_transactions returning {len(result_transactions)} transaction(s) (unlimited)")

    # Note: account_number filtering is not implemented for the pre-loaded data
    if account_number:
        logger.warning("Tool: get_transactions - account_number filter provided but ignored by the pre-loaded data source.")

    return result_transactions