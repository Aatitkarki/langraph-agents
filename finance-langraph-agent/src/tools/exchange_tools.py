from typing import Annotated, List, Optional, Dict
from langchain_core.tools import tool

# Import the mock data loaded in data_loader
from src.utils.data_loader import exchange_rates_data

@tool
def get_exchange_rates(currency_codes: Annotated[Optional[List[str]], "Optional list of currency codes (e.g., ['USD', 'EUR']) to retrieve rates for."]) -> List[Dict]:
    """
    Retrieves foreign exchange rates relative to QAR.
    If no codes are provided, returns all available rates.
    Each rate indicates how many QAR 1 unit of the foreign currency is worth (e.g., {'Code': 'USD', 'Rate': 3.65} means 1 USD = 3.65 QAR).
    """
    print(f"---Tool: get_exchange_rates called (Codes: {currency_codes})---")
    # Access the pre-loaded mock data
    all_rates = exchange_rates_data.get("ResponseData", [])
    if not all_rates:
        return [{"Error": "Exchange rate data not available."}]

    # Create a map of uppercase code to filtered rate data
    code_map = {
        rate['Code'].upper(): {
            "Code": rate.get("Code"),
            "Name": rate.get("Name"),
            "Rate": rate.get("Rate")
        }
        for rate in all_rates
    }

    if not currency_codes:
        # Return all filtered rates if no specific codes are requested
        result = list(code_map.values())
        print(f"---Tool: get_exchange_rates returning all rates: {result}---")
        return result
    else:
        # Filter for requested codes using the map
        requested_rates = []
        codes_to_check = [code.upper() for code in currency_codes]
        for code in codes_to_check:
            if code in code_map:
                requested_rates.append(code_map[code])
            else:
                # Note: Error message doesn't contain Name/Rate as they weren't found
                requested_rates.append({"Code": code, "Error": "Rate not found"})
        print(f"---Tool: get_exchange_rates returning requested rates: {requested_rates}---")
        return requested_rates