import logging
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.transaction_tools import get_transactions
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Define the Transaction History Agent
transaction_agent = create_react_agent(
    llm,
    tools=[get_transactions],
    prompt=finance_agent_system_prompt(
        "Retrieve and report transaction history for user accounts based on the user's request (e.g., last N transactions, specific date range - though mock data is limited)."
    )
)

logger.debug("--- Defined Transaction Agent ---") # Optional: for confirmation