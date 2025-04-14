import logging
from typing import List, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import dashboard_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_credit_card_details() -> List[Dict]:
    """Fetches details for all user credit cards from pre-loaded mock data. Returns a list of dictionaries, each containing card information such as NameOnCard, CardNo (masked), CardLimit, AvailableBalance, OutstandindBalance, PaymentDueDate, Status, and CardProductType."""
    logger.info("Tool: get_credit_card_details called")
    # Access the pre-loaded mock data
    data = dashboard_data.get("ResponseData", {}).get("Cards", [])
    if not data:
         error_msg = "No credit card data available."
         logger.error(f"Error in get_credit_card_details: {error_msg}")
         return [{"Error": error_msg}]
    return data