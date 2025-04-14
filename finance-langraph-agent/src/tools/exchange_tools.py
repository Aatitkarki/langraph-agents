import logging
from typing import Annotated, List, Optional, Dict
from langchain_core.tools import tool

# Import the exchange rate data loaded in data_loader
from src.utils.data_loader import exchange_rates_data

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def get_exchange_rates(currency_codes: Annotated[Optional[List[str]], "Optional list of currency codes (e.g., ['USD', 'EUR']) to retrieve rates for."]) -> List[Dict]:
    """
    Fetches foreign exchange (FX) rates relative to Qatari Riyal (QAR).

    This tool retrieves how many QAR are equivalent to one unit of a specified foreign currency,
    using pre-loaded exchange rate data.

    Args:
        currency_codes: An optional list of 3-letter ISO currency codes (e.g., ['USD', 'EUR']).
                        If provided, fetches rates only for these specific currencies.
                        If omitted or an empty list is passed, fetches rates for all available currencies.

    Returns:
        A list of dictionaries, where each dictionary contains the exchange rate information for one currency.
        - On success: {'Code': str, 'Name': str, 'Rate': float}
          Example: {'Code': 'USD', 'Name': 'US Dollar', 'Rate': 3.65} signifies that 1 US Dollar equals 3.65 Qatari Riyal.
        - If a requested code is not found: {'Code': str, 'Error': 'Rate not found'}
          Example: {'Code': 'XYZ', 'Error': 'Rate not found'}
    """
    logger.info(f"Tool: get_exchange_rates called (Codes: {currency_codes})")
    # Access the pre-loaded JSON data
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
        logger.info(f"Tool: get_exchange_rates returning all rates: {result}")
        return result
    else:
        # Filter for requested codes using the map
        requested_rates = []
        # Use a set to handle potential duplicate input codes and ensure case-insensitivity
        unique_codes_to_check = {code.upper() for code in currency_codes}
        for code in unique_codes_to_check:
            if code in code_map:
                requested_rates.append(code_map[code])
            else:
                # Note: Error message doesn't contain Name/Rate as they weren't found
                requested_rates.append({"Code": code, "Error": "Rate not found"})
        logger.info(f"Tool: get_exchange_rates returning requested rates: {requested_rates}")
        return requested_rates