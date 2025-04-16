import sys
import unittest.mock
from pathlib import Path
from typing import List, Dict, Any
import json # For comparing complex structures

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.card_tools import get_cards_details
# Import the actual mock data to verify the results
from src.utils.data_loader import dashboard_data

def compare_results(actual: List[Dict], expected: List[Dict]) -> bool:
    """
    Compares two lists of dictionaries, ignoring order.
    Sorts lists based on 'CardNo' before comparison.
    """
    if not isinstance(actual, list) or not isinstance(expected, list):
        print(f"Type mismatch: Actual ({type(actual)}) vs Expected ({type(expected)})")
        return False
    if len(actual) != len(expected):
        print(f"Length mismatch: Actual ({len(actual)}) vs Expected ({len(expected)})")
        return False

    # Sort both lists by 'CardNo' to ensure order doesn't affect comparison
    # Handle potential missing 'CardNo' key gracefully during sorting
    key_func = lambda x: x.get('CardNo', '') if isinstance(x, dict) else ''
    try:
        # Ensure all items are dictionaries before sorting
        if not all(isinstance(item, dict) for item in actual) or \
           not all(isinstance(item, dict) for item in expected):
             print("Comparison error: Not all items in lists are dictionaries.")
             return False
        sorted_actual = sorted(actual, key=key_func)
        sorted_expected = sorted(expected, key=key_func)
    except TypeError as e: # Handle cases where items might not be dicts or sort key fails
        print(f"Sorting error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected comparison error: {e}")
        return False


    # Use JSON dumps for a robust comparison of potentially nested structures
    actual_json = json.dumps(sorted_actual, sort_keys=True)
    expected_json = json.dumps(sorted_expected, sort_keys=True)

    if actual_json != expected_json:
        print("Content mismatch after sorting:")
        # print(f"  Expected JSON: {expected_json}") # Can be very verbose
        # print(f"  Actual JSON:   {actual_json}")
        return False

    return True


def run_card_test(expected: List[Dict], test_name: str = "get_cards_details()"):
    """Runs the test case for the get_cards_details tool."""
    print(f"Testing: {test_name}")
    try:
        # get_cards_details takes no arguments
        result = get_cards_details.invoke({})
        print(f"  Result Count: {len(result) if isinstance(result, list) else 'N/A'}") # Avoid printing large data

        if compare_results(result, expected):
            print("  Status: PASSED")
            return True
        else:
            print(f"  Status: FAILED")
            # Avoid printing potentially large expected/actual lists in failure message
            print(f"    Expected {len(expected)} card(s), got {len(result)} card(s). Content differs.")
            return False

    except Exception as e:
        print(f"  Test failed with unexpected exception: {type(e).__name__}: {str(e)}")
        print(f"  Status: FAILED (Expected list, got exception)")
        return False


def main():
    print("--- Running Card Tools Test ---")

    # Define expected results based on mock data structure
    # Fetch the expected full list directly from the loaded data
    expected_cards_data = dashboard_data.get("ResponseData", {}).get("Cards", None) # Use None to differentiate missing vs empty list

    if expected_cards_data is None:
        print("WARNING: 'Cards' key missing or 'ResponseData' missing in mock_data/dashboard_landing.json.")
        # The tool returns [{'Error': 'No card data available.'}] if the 'Cards' key is missing or data is empty dict
        expected_cards = [{"Error": "No card data available."}]
    elif not expected_cards_data: # Check if the list is empty []
         print("INFO: 'Cards' list is empty in mock_data/dashboard_landing.json.")
         expected_cards = [] # Tool returns empty list if 'Cards' is present but empty
    else:
        expected_cards = expected_cards_data # Use the actual card data

    passed_count = 0
    failed_count = 0

    # Test cases
    # 1. Normal case with cards data
    if run_card_test(expected_cards, "Normal case with cards data"):
        passed_count += 1
    else:
        failed_count += 1
    print("-" * 20) # Separator

    # 2. Test with None dashboard_data (mock this)
    original_data = dashboard_data
    try:
        import src.utils.data_loader
        src.utils.data_loader.dashboard_data = None
        if run_card_test([{"Error": "No card data available."}], "None dashboard_data"):
            passed_count += 1
        else:
            failed_count += 1
    finally:
        src.utils.data_loader.dashboard_data = original_data
    print("-" * 20)

    # 3. Test with missing Cards key
    try:
        src.utils.data_loader.dashboard_data = {"ResponseData": {}}
        if run_card_test([{"Error": "No card data available."}], "Missing Cards key"):
            passed_count += 1
        else:
            failed_count += 1
    finally:
        src.utils.data_loader.dashboard_data = original_data
    print("-" * 20)

    # 4. Test with malformed card data
    malformed_data = {
        "ResponseData": {
            "Cards": [
                {"Invalid": "Data"},  # Missing required fields
                {"CardNo": "1234", "NameOnCard": None}  # Invalid type
            ]
        }
    }
    with unittest.mock.patch('src.utils.data_loader.dashboard_data', malformed_data):
        expected = [
            {"Invalid": "Data"},
            {"CardNo": "1234", "NameOnCard": None}
        ]
        if run_card_test(expected, "Malformed card data"):
            passed_count += 1
        else:
            failed_count += 1
    print("-" * 20)

    print("\n--- Test Summary ---")
    print(f"Total tests: 4")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print("--- Test Completed ---")

    # Exit with non-zero code if any tests failed
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()