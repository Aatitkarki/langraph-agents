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
    tools=[get_exchange_rates, basic_calculator],
    prompt=finance_agent_system_prompt(
        "Retrieve exchange rates and perform currency conversions or other simple calculations using the python tool. "
        "All available rates are relative to QAR (e.g., 1 Foreign Currency = X QAR). "
        "To convert between two non-QAR currencies (e.g., USD to INR): "
        "1. Call 'get_exchange_rates' for BOTH the source and target currency codes (e.g., ['USD', 'INR']). "
        "2. Extract the 'Rate' for each from the results (e.g., rate_usd_to_qar, rate_inr_to_qar). Handle 'Rate not found' errors. "
        "3. Construct Python code for the calculation: `amount_in_qar = amount_source * rate_source_to_qar` followed by `final_amount = amount_in_qar / rate_target_to_qar`. "
        "4. Execute the code using 'python_repl_tool_finance'. "
        "5. Report the final converted amount. "
        "If converting to or from QAR, only one rate lookup is needed."
    )
)

logger.debug("--- Defined Exchange Rate Agent ---") # Optional: for confirmation