import logging
from typing import List, Dict
from langchain_core.tools import tool

# Import the data_loader module to access dashboard_data
import src.utils.data_loader

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_account_summary() -> List[Dict]:
    """Fetches a summary of all user accounts from pre-loaded JSON data.

    This tool retrieves a list of the user's accounts, including details about
    each account available in the pre-loaded dashboard dataset. The data is
    sourced from the ResponseData.Accounts section of the dashboard dataset.

    Args:
        None: This tool takes no parameters.

    Returns:
        List[Dict]: A list of account dictionaries with the following structure:
            - On success: Each dictionary contains account details including:
                * AccountNo: Internal account identifier
                * DisplayAccountNo: User-facing account number
                * AccountType: Type of account (e.g., 'Savings Account')
                * AvailableBalance: Current available balance
                * Currency: Account currency (e.g., 'QAR')
                * Status: Account status
                Example: {'DisplayAccountNo': '001-123456-001', 'AccountType': 'Savings Account', 'AvailableBalance': 15000.50, 'Currency': 'QAR'}
            - On error: Returns a list containing a single error dictionary:
                * Error: Description of the error
                Example: [{'Error': 'No account summary data available.'}]

    Error Handling:
        - Returns error dictionary if ResponseData or Accounts is missing
        - Logs errors to application logs
    """
    logger.info("Tool: get_account_summary called")
    
    # Handle None or empty dashboard_data case
    if not src.utils.data_loader.dashboard_data or src.utils.data_loader.dashboard_data.get("ResponseData") is None:
        error_msg = "No account summary data available."
        logger.error(f"Error in get_account_summary: {error_msg}")
        logger.debug(f"Returning error: {[{'Error': error_msg}]}")
        return [{"Error": error_msg}]

    # Access the ResponseData (default empty dict)
    response_data = src.utils.data_loader.dashboard_data.get("ResponseData", {})
    
    # Return error if Accounts is missing
    if "Accounts" not in response_data:
        error_msg = "No account summary data available."
        logger.error(f"Error in get_account_summary: {error_msg}")
        logger.debug(f"Returning error: {[{'Error': error_msg}]}")
        return [{"Error": error_msg}]
    
    accounts_data = response_data["Accounts"]
    
    # Return accounts data as-is (even if empty or malformed)
    logger.info(f"Tool: get_account_summary returning {len(accounts_data)} account(s)")
    logger.debug(f"Returning accounts data: {accounts_data}")
    return accounts_data