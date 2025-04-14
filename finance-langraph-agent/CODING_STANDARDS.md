# Project Coding Standards for LangChain/LangGraph Tools

This document outlines the coding standards and best practices to follow when creating or modifying tools within this project, particularly those intended for use with LangChain or LangGraph agents. Consistency helps maintainability and ensures tools behave predictably.

## 1. File Structure and Naming

- Tools should reside in the `src/tools/` directory.
- Each tool or closely related group of tools should be in its own Python file (e.g., `card_tools.py`, `exchange_tools.py`).
- File names should be descriptive and use snake_case (e.g., `account_tools.py`).
- Corresponding unit tests should be placed in the `tests/` directory with a matching name followed by `_test.py` (e.g., `tests/account_tools_test.py`).

## 2. Imports

- Organize imports in the following order:
  1.  Standard Python libraries (e.g., `logging`, `typing`, `json`).
  2.  Third-party libraries (e.g., `langchain_core`).
  3.  Project-specific modules (e.g., `from src.utils.data_loader import ...`).
- Import specific data variables needed from `src.utils.data_loader`.

## 3. Logging

- Instantiate a logger at the module level: `logger = logging.getLogger(__name__)`.
- Log the entry point of each tool function, including key parameters: `logger.info(f"Tool: {__name__} called (Param1: {param1}, ...)")`.
- Log successful results, potentially summarizing the output (e.g., number of items returned): `logger.info(f"Tool: {__name__} returning {len(data)} item(s)")`.
- Log errors encountered during execution: `logger.error(f"Error in {__name__}: {error_msg}")`.
- Log warnings for non-critical issues or assumptions (e.g., ignored parameters): `logger.warning("Tool: {__name__} - Parameter 'x' ignored...")`.

## 4. Tool Definition

- Use the `@tool` decorator from `langchain_core.tools` for functions intended to be used as tools by LLM agents.
- Function names should be descriptive, typically using a verb-noun pattern (e.g., `get_account_summary`, `get_exchange_rates`).

## 5. Function Signatures

- Use clear and descriptive parameter names.
- Apply Python type hints consistently (e.g., `List[Dict]`, `Optional[str]`, `int`).
- Use `typing.Annotated` for all tool function parameters to provide descriptions visible to the LLM. The annotation string should clearly explain the parameter's purpose and any constraints or notes (e.g., `Annotated[Optional[str], "Optional account number. NOTE: Currently ignored."]`).
- Provide default values (e.g., `= None`) for optional parameters directly in the signature.
- Specify the return type hint (e.g., `-> List[Dict]`).

## 6. Docstrings

- Use multi-line docstrings for all tool functions.
- **First Line:** A concise summary sentence describing the tool's primary function and data source (e.g., "Fetches ... from pre-loaded JSON data.").
- **Detailed Description:** A paragraph elaborating on the tool's purpose, how it works (at a high level), and the nature of the data it uses. Avoid using the word "mock"; refer to data as "pre-loaded", "sample", or "JSON data".
- **`Args:` Section:**
  - List each parameter using `parameter_name (type): Description.`.
  - Clearly explain the purpose and expected format of each argument. Include notes on default behavior or if a parameter is currently ignored by the implementation.
- **`Returns:` Section:**
  - Describe the structure of the successful return value (typically `List[Dict]`).
  - Provide details on the contents of the dictionaries within the list, including key field names and example values (`Example subset: {...}`).
  - Clearly document the structure and content of return values in case of errors (e.g., `Returns a list containing a single dictionary with an error message. Example: [{'Error': '...'}]`).

## 7. Data Handling

- Access pre-loaded data imported from `src.utils.data_loader`.
- Use `.get()` with default values (e.g., `.get("ResponseData", [])` or `.get("Key", {})`) for safe dictionary access to prevent `KeyError`.

## 8. Error Handling

- Check for expected data availability early in the function.
- If necessary data is missing, log an error and return a standardized error format (e.g., `[{"Error": "Descriptive error message."}]`). This provides a consistent failure signal to the agent.

## 9. Unit Testing (`tests/`)

- Create a corresponding test file for each tool file in the `tests/` directory.
- Import necessary modules, the tool function itself, and the relevant data from `src.utils.data_loader`.
- Include a `compare_results` helper function if comparing lists of dictionaries where order doesn't matter. This function should handle sorting based on a stable key (e.g., an ID, date, or name field). Use `json.dumps` for robust comparison of complex structures.
- Create a `run_<tool_name>_test` helper function to encapsulate the logic for running a single test case (invoking the tool with specific arguments and comparing the result to the expected output).
- The `main` function should:
  - Define expected results, often derived directly from the imported data source.
  - Define a list of test cases, covering different parameter combinations (e.g., `None` values, limits, specific filters, edge cases).
  - Iterate through test cases, calling the `run_<tool_name>_test` function.
  - Track and print a summary of passed/failed tests.
  - Use `sys.exit(1)` if any tests fail, suitable for CI/CD pipelines.
