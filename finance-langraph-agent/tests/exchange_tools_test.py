import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import json # For comparing complex structures

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.exchange_tools import get_exchange_rates
# We might need the actual mock data to verify the "all rates" case
from src.utils.data_loader import exchange_rates_data

def compare_results(actual: List[Dict], expected: List[Dict]) -> bool:
    """
    Compares two lists of dictionaries, ignoring order.
    Sorts lists based on 'Code' before comparison.
    """
    if not isinstance(actual, list) or not isinstance(expected, list):
        return False
    if len(actual) != len(expected):
        return False

    # Sort both lists by 'Code' to ensure order doesn't affect comparison
    # Handle potential missing 'Code' key gracefully during sorting
    key_func = lambda x: x.get('Code', '') if isinstance(x, dict) else ''
    try:
        sorted_actual = sorted(actual, key=key_func)
        sorted_expected = sorted(expected, key=key_func)
    except TypeError: # Handle cases where items might not be dicts
        return False

    # Use JSON dumps for a robust comparison of potentially nested structures
    return json.dumps(sorted_actual, sort_keys=True) == json.dumps(sorted_expected, sort_keys=True)


def run_test(currency_codes: Optional[List[str]], expected: List[Dict]):
    """Runs a single test case for the get_exchange_rates tool."""
    test_desc = f"Codes: {currency_codes}" if currency_codes is not None else "Codes: None (all rates)"
    print(f"Testing: {test_desc}")
    try:
        # Prepare arguments for invoke. Pass None explicitly if currency_codes is None.
        args = {"currency_codes": currency_codes}
        result = get_exchange_rates.invoke(args)
        print(f"  Result: {result}")

        if compare_results(result, expected):
            print("  Status: PASSED")
            return True
        else:
            # Use JSON dumps for clearer diff in failure message
            print(f"  Status: FAILED")
            print(f"    Expected: {json.dumps(expected, sort_keys=True)}")
            print(f"    Actual:   {json.dumps(result, sort_keys=True)}")
            return False

    except Exception as e:
        print(f"  Test failed with unexpected exception: {type(e).__name__}: {str(e)}")
        # If we expected a specific list but got an exception, it's a failure
        print(f"  Status: FAILED (Expected list, got exception)")
        return False


def main():
    print("--- Running Exchange Tools Test ---")

    # Define expected results based on mock data structure
    # Assuming mock data contains at least USD and EUR with known rates
    # Let's fetch the expected full list directly from the loaded data for the "all" case
    all_rates_expected = [
        {"Code": rate.get("Code"), "Name": rate.get("Name"), "Rate": rate.get("Rate")}
        for rate in exchange_rates_data.get("ResponseData", [])
    ]
    # Find specific rates for other test cases (handle potential missing keys)
    usd_rate = next((r for r in all_rates_expected if r.get("Code") == "USD"), {"Code": "USD", "Error": "Rate not found"})
    eur_rate = next((r for r in all_rates_expected if r.get("Code") == "EUR"), {"Code": "EUR", "Error": "Rate not found"})
    gbp_rate = next((r for r in all_rates_expected if r.get("Code") == "GBP"), {"Code": "GBP", "Error": "Rate not found"})


    test_cases = [
        # (input_codes, expected_output_list)
        (["USD", "EUR"], [usd_rate, eur_rate]),
        (["USD"], [usd_rate]),
        (["GBP", "USD"], [gbp_rate, usd_rate]),
        # Case-insensitivity
        (["usd", "eur"], [usd_rate, eur_rate]),
        # Non-existent code
        (["XYZ"], [{"Code": "XYZ", "Error": "Rate not found"}]),
        # Mix of existing and non-existent
        (["USD", "XYZ"], [usd_rate, {"Code": "XYZ", "Error": "Rate not found"}]),
        # Empty list - should return all
        ([], all_rates_expected),
        # None - should return all
        (None, all_rates_expected),
        # Duplicate codes (should return only one instance)
        (["USD", "USD"], [usd_rate]),
    ]

    passed_count = 0
    failed_count = 0

    for codes, expected in test_cases:
        if run_test(codes, expected):
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