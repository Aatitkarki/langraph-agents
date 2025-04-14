from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.card_tools import get_cards_details
from .prompts import finance_agent_system_prompt

# Define the Credit Card Agent
card_agent = create_react_agent(
    llm,
    tools=[get_cards_details],
    prompt=finance_agent_system_prompt(
        "Retrieve and report credit card details like balance, limit, and due dates based on the user's request."
    )
)

print("--- Defined Card Agent ---") # Optional: for confirmation