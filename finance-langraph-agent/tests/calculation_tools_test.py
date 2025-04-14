import sys
import math
from pathlib import Path
# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.calculation_tools import basic_calculator

def run_test(expression: str, expected: float | str):
    """Runs a single test case for the basic_calculator tool."""
    print(f"Testing expression: '{expression}'")
    try:
        result = basic_calculator.invoke({"expression": expression})
        print(f"  Result: {result}")

        if isinstance(expected, str): # Expecting an error message
            if isinstance(result, str) and expected in result:
                print("  Status: PASSED (Correct error message)")
                return True
            else:
                print(f"  Status: FAILED (Expected error containing '{expected}', got '{result}')")
                return False
        elif isinstance(result, float): # Expecting a numeric result
             # Use math.isclose for float comparison
            if math.isclose(result, expected, rel_tol=1e-9):
                 print("  Status: PASSED")
                 return True
            else:
                 print(f"  Status: FAILED (Expected {expected}, got {result})")
                 return False
        else: # Unexpected result type
            print(f"  Status: FAILED (Expected float {expected}, got type {type(result)}: {result})")
            return False

    except Exception as e:
        print(f"  Test failed with unexpected exception: {type(e).__name__}: {str(e)}")
        # If we expected an error string but got an exception, it might still be a failure
        if isinstance(expected, str):
             print(f"  Status: FAILED (Expected error message '{expected}', got exception)")
        else:
             print(f"  Status: FAILED (Expected numeric result {expected}, got exception)")
        return False


def main():
    print("--- Running Calculation Tools Test ---")
    test_cases = [
        ("10 + 5", 15.0),
        ("7 - 3", 4.0),
        ("15.5 * 3", 46.5),
        ("50 / 2", 25.0),
        ("10 / 4", 2.5),
        ("-5 + 2", -3.0),
        ("1.2 * 3.4", 4.08),
        # Error cases
        ("10 / 0", "Error: Division by zero."),
        ("10 +", "Error: Invalid expression format."),
        ("10 + 5 * 2", "Error: Invalid expression format."),
        ("10 ^ 2", "Error: Unsupported operator"),
        ("abc + 5", "Error: Invalid numbers"),
        ("10 * xyz", "Error: Invalid numbers"),
        ("10 /", "Error: Invalid expression format."),
        ("", "Error: Invalid expression format."),
    ]

    passed_count = 0
    failed_count = 0

    for expression, expected in test_cases:
        if run_test(expression, expected):
            passed_count += 1
        else:
            failed_count += 1
        print("-" * 20) # Separator

    print("\n--- Test Summary ---")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print("--- Test Completed ---")

    # Exit with non-zero code if any tests failed (useful for CI/CD)
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()