import os
import logging
import json

logger = logging.getLogger(__name__)

# --- Mock Data Loading ---
# Assumes JSON files are in a './mock_data/' subdirectory relative to the project root
mock_data_dir = "./mock_data"

def load_mock_data(filename: str) -> dict:
    """Loads mock data from a JSON file in the mock_data directory.

    Args:
        filename (str): Name of the JSON file to load from the mock_data directory.
                        Example: "dashboard_landing.json"

    Returns:
        dict: The parsed JSON data with the following structure:
            - On success: The full JSON content as a dictionary
            - On error: A dictionary with {"ResponseData": None} and logs the error

    Error Handling:
        - Handles FileNotFoundError by returning empty structure and logging warning
        - Handles JSONDecodeError by returning empty structure and logging warning
    """
    filepath = os.path.join(mock_data_dir, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f" Mock data file not found: {filepath}. Returning empty data.")
        # Return structure expected by tools if data is missing
        return {"ResponseData": None}
    except json.JSONDecodeError as e:
        logger.warning(f" Error decoding JSON from {filepath}. Details: {e}. Returning empty data.")
        return {"ResponseData": None}

# Global data variables loaded at startup
# These are imported by other modules to access pre-loaded data
#
# dashboard_data: Contains account and card summary information
# transactions_data: Contains transaction history records
# exchange_rates_data: Contains currency exchange rates
#
# Each variable will contain either:
# - The full parsed JSON data from its respective file
# - {"ResponseData": None} if loading failed
dashboard_data = load_mock_data("dashboard_landing.json")
transactions_data = load_mock_data("account_transactions.json")
exchange_rates_data = load_mock_data("exchange_rates.json")