import logging
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.exchange_tools import get_exchange_rates
from src.tools.calculation_tools import basic_calculator
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Define the Exchange Rate & Calculation Agent
exchange_rate_agent = create_react_agent(
    llm,
    tools=[get_exchange_rates, basic_calculator], # <-- Added RAG tool to list
    prompt=finance_agent_system_prompt(
        "Your task involves exchange rates and calculations. First, check if the user asks a general question about exchange rates or conversions (e.g., 'how does currency conversion work?', 'what is QAR?'). If so, use 'search_financial_docs'. "
        "If the user asks for specific rates or to perform a conversion/calculation (e.g., 'convert 100 USD to INR', 'what is USD rate?', 'calculate 5*10'), use 'get_exchange_rates' and/or 'basic_calculator'. "
        "Remember the multi-step process for non-QAR conversions: get both rates relative to QAR, then calculate using the calculator tool."
    )
)

logger.debug("--- Defined Exchange Rate Agent ---") # Optional: for confirmation