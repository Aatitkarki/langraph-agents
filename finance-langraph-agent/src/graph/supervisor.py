import logging
from typing import Callable, Literal, Type
from pydantic import BaseModel, create_model

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langgraph.graph import END
from langgraph.types import Command

# Import the shared state definition
from .state import FinancialAgentState

logger = logging.getLogger(f"{__name__}")

def create_supervisor_finance(llm: BaseChatModel, members: list[str])-> Callable[..., Command[str]]:
    """Creates a supervisor node function for routing between financial agents."""
    options = ["FINISH"] + members
    # system_prompt = (
    #     "You are a financial assistant supervisor. Your job is to understand the user's financial query "
    #     "and route it to the correct specialist agent, or handle general inquiries.\n"
    #     f"The available specialists and their functions are:\n"
    #     f"- account_agent: Handles queries about account summaries (balance, type).\n"
    #     f"- transaction_agent: Handles queries about transaction history.\n"
    #     f"- card_agent: Handles queries about credit card details (limit, balance, due date).\n"
    #     f"- exchange_rate_agent: Handles queries about currency exchange rates and performs conversions.\n\n"
    #     "Based on the user's request and the conversation history, choose the single next specialist agent to act.\n"
    #     "If the user asks a general question about capabilities (like 'what can you do?'), respond with 'FINISH' but first provide a brief summary of the available specialists and their functions in your reasoning process (this summary won't be shown to the user, but helps guide your decision). \n"
    #     "If the query has been fully answered by previous agents or cannot be answered by any specialist, respond with 'FINISH'.\n"
    #     f"Respond ONLY with the name of the next specialist agent ({', '.join([f'{m}' for m in members])}) or 'FINISH'." # Dynamically list members
    #     "Do not add any other explanation to your final output."
    # )
    system_prompt = (
        "You are a financial assistant supervisor. Your job is to orchestrate specialist agents to fulfill the user's financial query.\n"
        "Review the **entire conversation history** below, paying close attention to the **most recent message**.\n\n"
        f"The available specialists and their functions are:\n"
        f"- account_agent: Handles queries about account summaries (balance, type).\n"
        f"- transaction_agent: Handles queries about transaction history.\n"
        f"- card_agent: Handles queries about credit card details (limit, balance, due date).\n"
        f"- exchange_rate_agent: Handles queries about currency exchange rates and performs conversions.\n\n"
        "**Your Decision Process:**\n"
        "1. Examine the **original user request** and the **latest message** in the history.\n"
        "2. **If the latest message is from a specialist agent:** Does it directly and completely answer the specific task assigned to that agent?\n"
        "   - **If YES, and no other parts of the original user query remain unaddressed** by other specialists, respond with 'FINISH'. The specialist's last message contains the final answer.\n"
        "   - **If YES, but other parts of the original query still need a *different* specialist**, route to the appropriate next specialist.\n"
        "   - **If NO (the specialist couldn't answer or needs more info not available)**, decide if another specialist can help or if the query is unresolvable. Route to the next specialist or respond 'FINISH' if no further progress can be made.\n"
        "3. **If the latest message is from the user:** Determine which specialist is best suited to handle the newest request based on their capabilities. Route to that specialist.\n"
        "4. **General Queries:** If the user asks a general question about capabilities (like 'what can you do?'), respond with 'FINISH' but first provide a brief summary of the available specialists and their functions in your reasoning process (this summary won't be shown to the user, but helps guide your decision). \n"
        "5. **Completion:** If the query has been fully resolved by the history, or if no specialist can address the remaining request, respond with 'FINISH'.\n\n"
        f"**Output Format:** Respond ONLY with the 'FINISH' or name of the single next specialist agent ({', '.join([f'{m}' for m in members])}). Do not add any other explanation or text to your final output."
    )

    # Dynamically create the Pydantic model for the router
    Router: Type[BaseModel] = create_model(
        'Router',
        next=(Literal[tuple(options)], ...)
        # Config removed as title/description might not be needed for with_structured_output here
    )

    supervisor_chain = llm.with_structured_output(Router, include_raw=False)

    def supervisor_node(state: FinancialAgentState) -> Command[str]:
        """Routes work to the appropriate worker or finishes."""
        logger.debug("---Supervisor Running---")
        # Supervisor decides based on the conversation history
        # # Filter out tool messages for brevity if needed for the supervisor LLM call
        # supervisor_input_messages = [m for m in state['messages'] if not isinstance(m, ToolMessage)]
        supervisor_input_messages = state['messages']
        supervisor_input_messages = [SystemMessage(content=system_prompt)] + supervisor_input_messages

        logger.debug(f"input to llm: {supervisor_input_messages}")
        response = supervisor_chain.invoke(supervisor_input_messages)
        logger.debug(f"response from llm: {response}")

        # Explicitly check the type before accessing the attribute
        if isinstance(response, Router):
            next_worker = getattr(response, 'next', 'FINISH') # Use getattr as a fallback access method
        else:
            # Fallback if the response is not the expected Pydantic model
            logger.warning(f"Supervisor response type unexpected. Type: {type(response)}, Value: {response}")
            # Attempt dictionary access or default to FINISH
            try:
                next_worker = response.get("next", "FINISH") if isinstance(response, dict) else "FINISH"
            except Exception:
                 print("Error: Could not determine next worker from supervisor response.")
                 next_worker = "FINISH" # Default to FINISH on error
        logger.info(f"---Supervisor Decision: Route to {next_worker}---")
        if next_worker == "FINISH":
            return Command(goto=END, update={"next": None})
        else:
            # Ensure the chosen worker is actually in the members list before routing
            if next_worker in members:
                return Command(goto=next_worker, update={"next": next_worker})
            else:
                logger.warning(f"Error: Supervisor chose invalid worker '{next_worker}'. Defaulting to FINISH.")
                return Command(goto=END, update={"next": None}) # Go to END if invalid worker chosen
    return supervisor_node