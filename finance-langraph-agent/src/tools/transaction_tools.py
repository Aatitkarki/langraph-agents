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
    """Fetches the transaction history for the user from pre-loaded JSON data.

    This tool retrieves a list of transactions from the pre-loaded dataset. The data
    is sourced from the ResponseData section of the transactions dataset. While it
    accepts an account_number parameter for future compatibility, this filter is
    currently ignored by the pre-loaded data source.

    Args:
        account_number: An optional account number string (currently ignored).
        limit: An optional integer to limit the number of transactions returned.
               If omitted, all available transactions are returned.

    Returns:
        List[Dict]: A list of transaction dictionaries with the following structure:
            - On success: Each dictionary contains transaction details including:
                * TransactionDate: ISO 8601 timestamp of transaction
                * Description: Merchant or transaction description
                * Amount: Signed amount (negative for debits)
                * Currency: Transaction currency (e.g., 'QAR')
                * RunningBalance: Account balance after transaction
                * TransactionType: Type of transaction (e.g., 'POS', 'Transfer')
                Example: {'TransactionDate': '2024-07-15T10:30:00', 'Description': 'Grocery Store Purchase', 'Amount': -55.75, 'Currency': 'QAR'}
            - On error: Returns a list containing a single error dictionary:
                * Error: Description of the error
                Example: [{'Error': 'No transaction data available.'}]

    Error Handling:
        - Returns error dictionary if ResponseData is missing or empty
        - Logs warnings when account_number filter is ignored
        - Logs errors when no transaction data is available
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