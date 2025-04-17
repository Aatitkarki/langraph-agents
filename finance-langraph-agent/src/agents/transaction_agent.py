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
    tools=[get_transactions], # <-- Added RAG tool to list
    prompt=finance_agent_system_prompt(
        "Your task is related to transaction history. First, determine if the user is asking a general question about transactions (e.g., 'what are transaction types?', 'how do I view history?'). If so, use 'search_financial_docs' to answer from the knowledge base. If the user is asking for *their* specific transaction history (e.g., 'show my last 5 transactions', 'get history for account 456'), use the 'get_transactions' tool."
    )
)

logger.debug("--- Defined Transaction Agent ---") # Optional: for confirmation