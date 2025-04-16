import logging
import operator
import unicodedata
from typing import Annotated, Union
from langchain_core.tools import tool

# Define supported operators
_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
}

# Get a logger instance
logger = logging.getLogger(__name__)

@tool
def basic_calculator(
    expression: Annotated[str, "A simple arithmetic expression. Examples: '10 + 5', '100 * 2.5', '50 / 2', '7 - 3'"]
) -> Union[float, str]:
    """Performs basic arithmetic calculations (addition, subtraction, multiplication, division).

    This tool evaluates simple mathematical expressions with two operands and one operator.
    It supports the four basic arithmetic operations and handles common error cases.

    Args:
        expression: A string containing two numbers and one operator (+, -, *, /), separated by spaces.
                    Example: "15.5 * 3"
                    - Supports integers and floating point numbers
                    - Operators must be separated by spaces from numbers

    Returns:
        Union[float, str]: Either:
            - The numeric result of the calculation as a float
            - An error message string if the input is invalid

    Error Handling:
        - Returns error message for:
            * Invalid expression format (not 'number operator number')
            * Non-numeric operands
            * Unsupported operators
            * Division by zero
            * Other unexpected errors
        - Logs all errors with full context
    """
    logger.info(f"Tool: basic_calculator executing expression: {expression}")
    try:
        parts = expression.split()
        if len(parts) != 3:
            error_msg = "Error: Invalid expression format. Use 'number operator number' (e.g., '10 + 5')."
            logger.error(f"{error_msg} (Expression: '{expression}')")
            return error_msg

        num1_str, op_str, num2_str = parts

        def normalize_number(num_str: str) -> str:
            """Normalizes non-ASCII numbers to standard ASCII numbers.
            
            Handles:
            - Fullwidth numbers (e.g., '１０' → '10')
            - Arabic numerals (e.g., '١٠' → '10')
            """
            try:
                # First try direct conversion for standard numbers
                float(num_str)
                return num_str
            except ValueError:
                # Try normalizing non-ASCII digits
                normalized = []
                for c in num_str:
                    if c.isdigit() or c in ('.', '-', '+'):
                        # Convert digit characters to their ASCII equivalents
                        if c.isdigit():
                            digit = unicodedata.digit(c)
                            normalized.append(str(digit))
                        else:
                            normalized.append(c)
                    else:
                        raise ValueError(f"Invalid number character: '{c}'")
                return ''.join(normalized)

        try:
            num1 = float(normalize_number(num1_str))
            num2 = float(normalize_number(num2_str))
        except ValueError as e:
            error_msg = f"Error: Invalid numbers in expression. {str(e)}"
            logger.error(f"{error_msg} (Expression: '{expression}')")
            return error_msg

        if op_str not in _OPERATORS:
            error_msg = f"Error: Unsupported operator '{op_str}'. Use one of: {', '.join(_OPERATORS.keys())}"
            logger.error(f"{error_msg} (Expression: '{expression}')")
            return error_msg

        if op_str == "/" and num2 == 0:
            error_msg = "Error: Division by zero."
            logger.error(f"{error_msg} (Expression: '{expression}')")
            return error_msg

        calculate = _OPERATORS[op_str]
        result = calculate(num1, num2)
        return float(result)

    except Exception as e:
        error_msg = f"An unexpected error occurred: {repr(e)}"
        logger.exception(f"{error_msg} (Expression: '{expression}')") # Use exception to include traceback
        return error_msg