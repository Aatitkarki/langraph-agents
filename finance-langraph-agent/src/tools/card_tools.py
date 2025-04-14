from typing import List, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import dashboard_data

@tool
def get_credit_card_details() -> List[Dict]:
    """Retrieves details about the user's credit cards, including limits, balances, and due dates."""
    print("---Tool: get_credit_card_details called---")
    # Access the pre-loaded mock data
    data = dashboard_data.get("ResponseData", {}).get("Cards", [])
    if not data:
         return [{"Error": "No credit card data available."}]
    return data