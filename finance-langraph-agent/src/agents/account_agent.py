import logging

from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.account_tools import get_account_summary
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Define the Account Information Agent
account_agent = create_react_agent(
    llm,
    tools=[get_account_summary], # <-- Added RAG tool to list
    prompt=finance_agent_system_prompt(
        """
        Your task is related to user accounts. First, determine if the user is asking a general question about accounts (e.g., 'how do I find my balance?', 'what is an account summary?'). 
        If so, politely decline i am not capable of doing it.
        If the user is asking for specific details about *their* account (e.g., 'what is MY balance?', 'get summary for account 123'), use the 'get_account_summary' tool."
        """
    )
)

logger.debug("--- Defined Account Agent ---") # Optional: for confirmation during loading