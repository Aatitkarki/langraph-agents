import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

# Import necessary components from other modules
from src.utils.llm_config import llm
from src.tools.card_tools import get_cards_details
from .prompts import finance_agent_system_prompt

logger = logging.getLogger(__name__)

# Task description for this agent
CARD_AGENT_TASK = """
Your task is related to credit cards. First, determine if the user is asking a general question about cards (e.g., 'how do I find my limit?', 'explain credit card balance').
If the user is asking for *their* specific card details (e.g., 'what is MY card balance?', 'get details for card ending 1234'), use the 'get_cards_details' tool.
If the user asks a general question that might be answerable with the provided context, use the context to formulate a helpful response. If the context doesn't help, state that you can only provide specific card details using the tool.
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
        task_description=CARD_AGENT_TASK,
        rag_context=input_dict.get("rag_context") # Access rag_context from input
    )
)

# Define the Credit Card Agent using the dynamic prompt
card_agent = create_react_agent(
    llm,
    tools=[get_cards_details],
    prompt=prompt_template
)

logger.debug("--- Defined Card Agent with Dynamic Prompt ---")