from typing import Annotated
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

# Python REPL Tool (for calculations like currency conversion)
repl = PythonREPL()

@tool
def python_repl_tool_finance(
    code: Annotated[str, "The python code to execute for calculations like currency conversion."],
):
    """Use this to execute python code for financial calculations.
       Make sure to use the provided exchange rates if needed by fetching them first.
       If you want to see the output of a value, print it out with `print(...)`.
       This is visible to the user. Wrap the final result in the print() statement.
    """
    print(f"---Tool: python_repl_tool_finance executing code:\n{code}\n---")
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute code. Error: {repr(e)}"
    return f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"