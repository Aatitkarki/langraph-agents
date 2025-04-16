import logging
from typing import List, Dict
from langchain_core.tools import tool

# Get a logger instance
logger = logging.getLogger(__name__)

def get_dashboard_data():
    """Helper function to get current dashboard data.
    Allows proper mocking during tests."""
    from src.utils.data_loader import dashboard_data
    return dashboard_data

@tool
def get_cards_details() -> List[Dict]:
    """Fetches details for all user credit and debit cards from pre-loaded JSON data.

    This tool retrieves comprehensive information about the user's cards available in the
    pre-loaded dashboard dataset. The data is sourced from the ResponseData.Cards section.

    Args:
        None: This tool takes no parameters.

    Returns:
        List[Dict]: A list of card dictionaries with the following structure:
            - On success: Each dictionary contains card details including:
                * NameOnCard: Cardholder name
                * CardNo: Masked card number (e.g., '4324 XXXX XXXX 5884')
                * CardLimit: Total credit limit
                * AvailableBalance: Available credit
                * OutstandingBalance: Current balance
                * PaymentDueDate: Next payment due date
                * Status: Card status (e.g., 'Active')
                * CardProductType: Type of card (e.g., 'Visa Infinite')
                Example: {'NameOnCard': 'HUSSEIN MODAK', 'CardNo': '4324 XXXX XXXX 5884', 'AvailableBalance': 2552474.83, 'Status': 'Active'}
            - On error: Returns a list containing a single error dictionary:
                * Error: Description of the error
                Example: [{'Error': 'No card data available.'}]

    Error Handling:
        - Returns error dictionary if ResponseData or Cards is missing
        - Logs errors to application logs
    """
    logger.info("Tool: get_cards_details called")
    dashboard_data = get_dashboard_data()
    
    # Handle None dashboard_data case
    if dashboard_data is None:
        error_msg = "No card data available."
        logger.error(f"Error in get_cards_details: {error_msg}")
        return [{"Error": error_msg}]
    
    # Access the current dashboard data
    response_data = dashboard_data.get("ResponseData", {})
    data = response_data.get("Cards")
    
    # Handle missing Cards key
    if data is None:
        error_msg = "No card data available."
        logger.error(f"Error in get_cards_details: {error_msg}")
        return [{"Error": error_msg}]
    
    # Return empty list if Cards exists but is empty
    if not data:
        logger.info("Tool: get_cards_details - empty card list")
        return []
    
    logger.info(f"Tool: get_cards_details returning {len(data)} card(s)")
    return data