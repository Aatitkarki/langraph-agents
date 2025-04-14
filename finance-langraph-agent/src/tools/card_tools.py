import logging
from typing import List, Dict
from langchain_core.tools import tool

# Import the dashboard data loaded in data_loader
from src.utils.data_loader import dashboard_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_cards_details() -> List[Dict]:
    """
    Fetches details for all user credit and potentially other cards from pre-loaded JSON data.

    This tool retrieves comprehensive information about the user's cards available in the
    pre-loaded dashboard dataset.

    Returns:
        A list of dictionaries, where each dictionary contains details for one card.
        - On success: Each dictionary includes fields like NameOnCard, CardNo (masked),
          CardLimit, AvailableBalance, OutstandindBalance, PaymentDueDate, Status,
          CardProductType, etc.
          Example subset: {'NameOnCard': 'HUSSEIN MODAK', 'CardNo': '4324 XXXX XXXX 5884', 'AvailableBalance': 2552474.83, 'Status': 'Active'}
        - If no card data is found: Returns a list containing a single dictionary with an error message.
          Example: [{'Error': 'No card data available.'}]
    """
    logger.info("Tool: get_cards_details called")
    # Access the pre-loaded JSON data
    data = dashboard_data.get("ResponseData", {}).get("Cards", [])
    if not data:
         error_msg = "No card data available."
         logger.error(f"Error in get_cards_details: {error_msg}")
         return [{"Error": error_msg}]
    logger.info(f"Tool: get_cards_details returning {len(data)} card(s)")
    return data