import logging
from typing import List, Dict
from langchain_core.tools import tool

# Import the dashboard data loaded in data_loader
from src.utils.data_loader import dashboard_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_account_summary() -> List[Dict]:
    """
    Fetches a summary of all user accounts from pre-loaded JSON data.

    This tool retrieves a list of the user's accounts, including details about
    each account available in the pre-loaded dashboard dataset.

    Returns:
        A list of dictionaries, where each dictionary contains details for one account.
        - On success: Each dictionary includes fields like AccountNo, DisplayAccountNo,
          AccountType, AvailableBalance, Currency, Status, etc.
          Example subset: {'DisplayAccountNo': '001-123456-001', 'AccountType': 'Savings Account', 'AvailableBalance': 15000.50, 'Currency': 'QAR'}
        - If no account data is found: Returns a list containing a single dictionary with an error message.
          Example: [{'Error': 'No account summary data available.'}]
    """
    logger.info("Tool: get_account_summary called")
    # Access the pre-loaded JSON data
    accounts_data = dashboard_data.get("ResponseData", {}).get("Accounts", [])
    if not accounts_data:
         error_msg = "No account summary data available."
         logger.error(f"Error in get_account_summary: {error_msg}")
         return [{"Error": error_msg}]

    logger.info(f"Tool: get_account_summary returning {len(accounts_data)} account(s)")
    # Returning the full data as per the original implementation
    return accounts_data