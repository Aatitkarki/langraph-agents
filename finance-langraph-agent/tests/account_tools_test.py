import sys
from pathlib import Path
from typing import List, Dict, Any
import json # For comparing complex structures

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.account_tools import get_account_summary
# Import the actual mock data to verify the results
from src.utils.data_loader import dashboard_data

def compare_results(actual: List[Dict], expected: List[Dict]) -> bool:
    """
    Compares two lists of account dictionaries, ignoring order.
    Sorts lists based on 'DisplayAccountNo' before comparison.
    """
    if not isinstance(actual, list) or not isinstance(expected, list):
        print(f"Type mismatch: Actual ({type(actual)}) vs Expected ({type(expected)})")
        return False
    if len(actual) != len(expected):
        print(f"Length mismatch: Actual ({len(actual)}) vs Expected ({len(expected)})")
        return False

    # Sort both lists by 'DisplayAccountNo' for stable sorting
    key_func = lambda x: x.get('DisplayAccountNo', '') if isinstance(x, dict) else ''
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
        # Avoid printing potentially large lists
        # print(f"  Expected JSON: {expected_json}")
        # print(f"  Actual JSON:   {actual_json}")
        return False

    return True


def run_account_test(expected: List[Dict]):
    """Runs the test case for the get_account_summary tool."""
    print("Testing: get_account_summary()")
    try:
        # get_account_summary takes no arguments
        result = get_account_summary.invoke({})
        print(f"  Result Count: {len(result) if isinstance(result, list) else 'N/A'}") # Avoid printing large data

        if compare_results(result, expected):
            print("  Status: PASSED")
            return True
        else:
            print(f"  Status: FAILED")
            # Avoid printing potentially large expected/actual lists in failure message
            print(f"    Expected {len(expected)} account(s), got {len(result)} account(s). Content differs.")
            return False

    except Exception as e:
        print(f"  Test failed with unexpected exception: {type(e).__name__}: {str(e)}")
        print(f"  Status: FAILED (Expected list, got exception)")
        return False


def main():
    print("--- Running Account Tools Test ---")

    # Define expected results based on mock data structure
    # Fetch the expected full list directly from the loaded data
    expected_accounts_data = dashboard_data.get("ResponseData", {}).get("Accounts", None) # Use None to differentiate missing vs empty list

    if expected_accounts_data is None:
        print("WARNING: 'Accounts' key missing or 'ResponseData' missing in mock_data/dashboard_landing.json.")
        # The tool returns [{'Error': 'No account summary data available.'}] if the 'Accounts' key is missing or data is empty dict
        expected_accounts = [{"Error": "No account summary data available."}]
    elif not expected_accounts_data: # Check if the list is empty []
         print("INFO: 'Accounts' list is empty in mock_data/dashboard_landing.json.")
         expected_accounts = [] # Tool returns empty list if 'Accounts' is present but empty
    else:
        expected_accounts = expected_accounts_data # Use the actual account data


    passed_count = 0
    failed_count = 0

    # Only one main test case: fetch all accounts
    if run_account_test(expected_accounts):
        passed_count += 1
    else:
        failed_count += 1
    print("-" * 20) # Separator

    print("\n--- Test Summary ---")
    print(f"Total tests: 1") # Only one test case for now
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print("--- Test Completed ---")

    # Exit with non-zero code if any tests failed
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()