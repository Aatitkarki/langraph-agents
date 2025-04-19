import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.exchange_tools import get_exchange_rates
from src.tools.calculation_tools import basic_calculator
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Task description for this agent
EXCHANGE_RATE_AGENT_TASK = """
Your task involves exchange rates and calculations. First, check if the user asks a general question about exchange rates or conversions (e.g., 'how does currency conversion work?', 'what is QAR?').
If the user asks for specific rates or to perform a conversion/calculation (e.g., 'convert 100 USD to INR', 'what is USD rate?', 'calculate 5*10'), use 'get_exchange_rates' and/or 'basic_calculator'.
Remember the multi-step process for non-QAR conversions: get both rates relative to QAR, then calculate using the calculator tool.
If the user asks a general question that might be answerable with the provided context, use the context to formulate a helpful response. If the context doesn't help, state that you can only provide specific rates/calculations using the tools.
"""

# Create a dynamic prompt template
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", ""), # Placeholder, will be replaced by the lambda function below
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
).partial(
    system_message=lambda input_dict: finance_agent_system_prompt(
        task_description=EXCHANGE_RATE_AGENT_TASK,
        rag_context=input_dict.get("rag_context") # Access rag_context from input
    )
)

# Define the Exchange Rate & Calculation Agent using the dynamic prompt
exchange_rate_agent = create_react_agent(
    llm,
    tools=[get_exchange_rates, basic_calculator],
    prompt=prompt_template
)

logger.debug("--- Defined Exchange Rate Agent with Dynamic Prompt ---")