import os
import json

# --- Mock Data Loading ---
# Assumes JSON files are in a './mock_data/' subdirectory relative to the project root
mock_data_dir = "./mock_data"

def load_mock_data(filename: str) -> dict:
    """Loads mock data from a JSON file with basic error handling."""
    filepath = os.path.join(mock_data_dir, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Mock data file not found: {filepath}. Returning empty data.")
        # Return structure expected by tools if data is missing
        return {"ResponseData": None}
    except json.JSONDecodeError as e:
        print(f"Warning: Error decoding JSON from {filepath}. Details: {e}. Returning empty data.")
        return {"ResponseData": None}

# Load all mock data at the start so it's available for import
dashboard_data = load_mock_data("dashboard_landing.json")
transactions_data = load_mock_data("account_transactions.json")
exchange_rates_data = load_mock_data("exchange_rates.json")