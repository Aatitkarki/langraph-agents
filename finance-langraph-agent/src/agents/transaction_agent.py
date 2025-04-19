import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.transaction_tools import get_transactions
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Task description for this agent
TRANSACTION_AGENT_TASK = """
Your task is related to transaction history. First, determine if the user is asking a general question about transactions (e.g., 'what are transaction types?', 'how do I view history?').
If the user is asking for *their* specific transaction history (e.g., 'show my last 5 transactions', 'get history for account 456'), use the 'get_transactions' tool.
If the user asks a general question that might be answerable with the provided context, use the context to formulate a helpful response. If the context doesn't help, state that you can only provide specific transaction history using the tool.
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
        task_description=TRANSACTION_AGENT_TASK,
        rag_context=input_dict.get("rag_context") # Access rag_context from input
    )
)

# Define the Transaction History Agent using the dynamic prompt
transaction_agent = create_react_agent(
    llm,
    tools=[get_transactions],
    prompt=prompt_template
)

logger.debug("--- Defined Transaction Agent with Dynamic Prompt ---")