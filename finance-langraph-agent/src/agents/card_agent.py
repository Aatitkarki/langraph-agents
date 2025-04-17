import logging
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.card_tools import get_cards_details
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Define the Credit Card Agent
card_agent = create_react_agent(
    llm,
    tools=[get_cards_details], # <-- Added RAG tool to list
    prompt=finance_agent_system_prompt(
        "Your task is related to credit cards. First, determine if the user is asking a general question about cards (e.g., 'how do I find my limit?', 'explain credit card balance'). If so, use 'search_financial_docs' to answer from the knowledge base. If the user is asking for *their* specific card details (e.g., 'what is MY card balance?', 'get details for card ending 1234'), use the 'get_cards_details' tool."
    )
)

logger.debug("--- Defined Card Agent ---") # Optional: for confirmation