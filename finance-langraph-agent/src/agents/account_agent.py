import logging

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
 
from langgraph.prebuilt import create_react_agent
 
# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.account_tools import get_account_summary
from .prompts import finance_agent_system_prompt
# Import state for type hinting if needed, though create_react_agent handles input dict
# from src.graph.state import FinancialAgentState
 
logger = logging.getLogger(__name__)
 
# Task description for this agent
ACCOUNT_AGENT_TASK = """
Your task is related to user accounts. First, determine if the user is asking a general question about accounts (e.g., 'how do I find my balance?', 'what is an account summary?').
If the user is asking for specific details about *their* account (e.g., 'what is MY balance?', 'get summary for account 123'), use the 'get_account_summary' tool.
If the user asks a general question that might be answerable with the provided context, use the context to formulate a helpful response. If the context doesn't help, state that you can only provide specific account summaries using the tool.
"""
 
# Create a dynamic prompt template
# It expects the input dictionary to create_react_agent to contain 'messages' and optionally 'rag_context'
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", ""), # Placeholder, will be replaced by the lambda function below
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
).partial(
    system_message=lambda input_dict: finance_agent_system_prompt(
        task_description=ACCOUNT_AGENT_TASK,
        rag_context=input_dict.get("rag_context") # Access rag_context from input
    )
)

# Define the Account Information Agent using the dynamic prompt
account_agent = create_react_agent(
    llm,
    tools=[get_account_summary],
    prompt=prompt_template
)
 
logger.debug("--- Defined Account Agent with Dynamic Prompt ---")