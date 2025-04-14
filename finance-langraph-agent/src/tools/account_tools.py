from typing import List, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import dashboard_data

@tool
def get_account_summary() -> List[Dict]:
    """Retrieves the summary of the user's accounts, including balance and type."""
    print("---Tool: get_account_summary called---")
    # Access the pre-loaded mock data
    data = dashboard_data.get("ResponseData", {}).get("Accounts", [])
    if not data:
         return [{"Error": "No account summary data available."}]
    # Optionally filter/simplify the data returned to the agent
    # simplified_data = [{"AccountNo": acc.get("DisplayAccountNo"), "Balance": acc.get("AvailableBalance"), "Type": acc.get("AccountType")} for acc in data]
    # return simplified_data
    return data # Returning full data for now