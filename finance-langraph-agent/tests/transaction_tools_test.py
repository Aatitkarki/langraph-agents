import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json # For comparing complex structures

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.transaction_tools import get_transactions
# Import the actual mock data to verify the results
from src.utils.data_loader import transactions_data

def compare_results(actual: List[Dict], expected: List[Dict]) -> bool:
    """
    Compares two lists of transaction dictionaries, ignoring order.
    Sorts lists based on 'TransactionDate' then 'Description' before comparison.
    """
    if not isinstance(actual, list) or not isinstance(expected, list):
        print(f"Type mismatch: Actual ({type(actual)}) vs Expected ({type(expected)})")
        return False
    if len(actual) != len(expected):
        print(f"Length mismatch: Actual ({len(actual)}) vs Expected ({len(expected)})")
        return False

    # Sort both lists by 'TransactionDate', then 'Description' for stable sorting
    key_func = lambda x: (x.get('TransactionDate', ''), x.get('Description', '')) if isinstance(x, dict) else ('', '')
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


def run_transaction_test(account_number: Optional[str], limit: Optional[int], expected: List[Dict]):
    """Runs a single test case for the get_transactions tool."""
    test_desc = f"Account: {account_number}, Limit: {limit}"
    print(f"Testing: {test_desc}")
    try:
        args = {}
        if account_number is not None:
            args["account_number"] = account_number
        if limit is not None:
            args["limit"] = limit

        result = get_transactions.invoke(args)
        print(f"  Result Count: {len(result) if isinstance(result, list) else 'N/A'}")

        if compare_results(result, expected):
            print("  Status: PASSED")
            return True
        else:
            print(f"  Status: FAILED")
            print(f"    Expected {len(expected)} transaction(s), got {len(result)} transaction(s). Content differs.")
            return False

    except Exception as e:
        print(f"  Test failed with unexpected exception: {type(e).__name__}: {str(e)}")
        print(f"  Status: FAILED (Expected list, got exception)")
        return False


def main():
    print("--- Running Transaction Tools Test ---")

    # Save original data for restoration after tests
    original_data = transactions_data

    # Standard test cases with original data
    all_transactions_data = transactions_data.get("ResponseData", None)

    if all_transactions_data is None:
        print("WARNING: 'ResponseData' missing in mock transaction data.")
        expected_all = [{"Error": "No transaction data available."}]
        expected_limited = expected_all # Error state doesn't change with limit
    elif not all_transactions_data: # Check if the list is empty []
         print("INFO: 'ResponseData' list is empty in mock transaction data.")
         expected_all = []
         expected_limited = []
    else:
        expected_all = all_transactions_data
        # Calculate expected limited results
        limit_val = 5 # Example limit for testing
        expected_limited = expected_all[:limit_val] if len(expected_all) >= limit_val else expected_all

    test_cases = [
        # (account_number, limit, expected_output_list)
        # Test case 1: Get all transactions (limit=None)
        (None, None, expected_all),
        # Test case 2: Get limited transactions
        (None, 5, expected_limited),
        # Test case 3: Get all transactions with account number (ignored)
        ("ACC123", None, expected_all),
        # Test case 4: Get limited transactions with account number (ignored)
        ("ACC123", 5, expected_limited),
        # Test case 5: Limit greater than available transactions
        (None, 1000, expected_all),
         # Test case 6: Limit = 0 (should return all as per current logic)
        (None, 0, expected_all),
         # Test case 7: Limit = -1 (should return all as per current logic)
        (None, -1, expected_all),
    ]

    # Additional test cases that modify the data
    additional_test_cases = [
        # Test with None transactions_data
        (None, None, None, [{"Error": "No transaction data available."}]),
        # Test with malformed transaction data
        ({"ResponseData": [
            {"TransactionDate": "invalid", "Description": None, "Amount": "NaN"},
            {"TransactionDate": "2024-01-01", "Description": "Valid", "Amount": 100}
        ]}, None, None, [
            {"TransactionDate": "invalid", "Description": None, "Amount": "NaN"},
            {"TransactionDate": "2024-01-01", "Description": "Valid", "Amount": 100}
        ]),
        # Test with large amounts
        ({"ResponseData": [
            {"TransactionDate": "2024-01-01", "Description": "Large", "Amount": 1e12}
        ]}, None, None, [
            {"TransactionDate": "2024-01-01", "Description": "Large", "Amount": 1e12}
        ]),
        # Test with special characters
        ({"ResponseData": [
            {"TransactionDate": "2024-01-01", "Description": "日本料理店", "Amount": 500}
        ]}, None, None, [
            {"TransactionDate": "2024-01-01", "Description": "日本料理店", "Amount": 500}
        ]),
    ]

    passed_count = 0
    failed_count = 0

    # Run standard test cases
    for acc_num, lim, expected in test_cases:
        if run_transaction_test(acc_num, lim, expected):
            passed_count += 1
        else:
            failed_count += 1
        print("-" * 20) # Separator

    # Run additional test cases that modify the data
    import src.utils.data_loader
    for test_data, acc_num, lim, expected in additional_test_cases:
        try:
            if test_data is None:
                src.utils.data_loader.transactions_data = None
            else:
                src.utils.data_loader.transactions_data = test_data
            
            if run_transaction_test(acc_num, lim, expected):
                passed_count += 1
            else:
                failed_count += 1
            print("-" * 20) # Separator
        finally:
            src.utils.data_loader.transactions_data = original_data

    passed_count = 0
    failed_count = 0

    for acc_num, lim, expected in test_cases:
        # Adjust expectation based on actual data state if needed
        current_expected = expected
        if all_transactions_data is None:
             current_expected = [{"Error": "No transaction data available."}]
        elif not all_transactions_data:
             current_expected = []


        if run_transaction_test(acc_num, lim, current_expected):
            passed_count += 1
        else:
            failed_count += 1
        print("-" * 20) # Separator

    print("\n--- Test Summary ---")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print("--- Test Completed ---")

    # Exit with non-zero code if any tests failed
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()