from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.account_tools import get_account_summary
from .prompts import finance_agent_system_prompt

# Define the Account Information Agent
account_agent = create_react_agent(
    llm,
    tools=[get_account_summary],
    prompt=finance_agent_system_prompt(
        "Retrieve and report account summary information like balance, account number, and type based on the user's request."
    )
)

print("--- Defined Account Agent ---") # Optional: for confirmation during loading