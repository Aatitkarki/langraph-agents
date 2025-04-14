import logging
from typing import List, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import dashboard_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_account_summary() -> List[Dict]:
    """Retrieves the summary of the user's accounts, including balance and type."""
    logger.info("Tool: get_account_summary called")
    # Access the pre-loaded mock data
    data = dashboard_data.get("ResponseData", {}).get("Accounts", [])
    if not data:
         error_msg = "No account summary data available."
         logger.error(f"Error in get_account_summary: {error_msg}")
         return [{"Error": error_msg}]
    # Optionally filter/simplify the data returned to the agent
    # simplified_data = [{"AccountNo": acc.get("DisplayAccountNo"), "Balance": acc.get("AvailableBalance"), "Type": acc.get("AccountType")} for acc in data]
    # return simplified_data
    return data # Returning full data for now