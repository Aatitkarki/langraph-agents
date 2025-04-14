import logging
import operator
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
    """
    Performs basic arithmetic calculations (addition, subtraction, multiplication, division).

    Args:
        expression: A string containing two numbers and one operator (+, -, *, /), separated by spaces.
                    Example: "15.5 * 3"

    Returns:
        The result of the calculation as a float, or an error message string if the input is invalid.
    """
    logger.info(f"Tool: basic_calculator executing expression: {expression}")
    try:
        parts = expression.split()
        if len(parts) != 3:
            error_msg = "Error: Invalid expression format. Use 'number operator number' (e.g., '10 + 5')."
            logger.error(f"{error_msg} (Expression: '{expression}')")
            return error_msg

        num1_str, op_str, num2_str = parts

        try:
            num1 = float(num1_str)
            num2 = float(num2_str)
        except ValueError:
            error_msg = f"Error: Invalid numbers in expression. Could not convert '{num1_str}' or '{num2_str}'."
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