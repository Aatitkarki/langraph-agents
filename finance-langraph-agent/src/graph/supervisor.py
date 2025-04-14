from typing import Callable, Literal, Type
from pydantic import BaseModel, create_model

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.graph import END
from langgraph.types import Command

# Import the shared state definition
from .state import FinancialAgentState

def create_supervisor_finance(llm: BaseChatModel, members: list[str])-> Callable[..., Command[str]]:
    """Creates a supervisor node function for routing between financial agents."""
    options = ["FINISH"] + members
    system_prompt = (
        "You are a financial assistant supervisor. Your job is to understand the user's financial query "
        "and route it to the correct specialist agent, or handle general inquiries.\n"
        f"The available specialists and their functions are:\n"
        f"- account_agent: Handles queries about account summaries (balance, type).\n"
        f"- transaction_agent: Handles queries about transaction history.\n"
        f"- card_agent: Handles queries about credit card details (limit, balance, due date).\n"
        f"- exchange_rate_agent: Handles queries about currency exchange rates and performs conversions.\n\n"
        "Based on the user's request and the conversation history, choose the single next specialist agent to act.\n"
        "If the user asks a general question about capabilities (like 'what can you do?'), respond with 'FINISH' but first provide a brief summary of the available specialists and their functions in your reasoning process (this summary won't be shown to the user, but helps guide your decision). \n"
        "If the query has been fully answered by previous agents or cannot be answered by any specialist, respond with 'FINISH'.\n"
        f"Respond ONLY with the name of the next specialist agent ({', '.join([f'{m}' for m in members])}) or 'FINISH'." # Dynamically list members
        "Do not add any other explanation to your final output."
    )

    # No Router model needed, we'll parse the raw string output
    supervisor_chain = llm # Use the base LLM directly

    def supervisor_node(state: FinancialAgentState) -> Command[str]:
        """Routes work to the appropriate worker or finishes."""
        print("---Supervisor Running---")
        # Supervisor decides based on the conversation history
        # # Filter out tool messages for brevity if needed for the supervisor LLM call
        # supervisor_input_messages = [m for m in state['messages'] if not isinstance(m, ToolMessage)]
        supervisor_input_messages = state['messages']
        supervisor_input_messages = [HumanMessage(content=system_prompt)] + supervisor_input_messages

        # Invoke the base LLM and get the raw content
        response_msg = supervisor_chain.invoke(supervisor_input_messages)
        # Ensure response_msg has content attribute (should be AIMessage)
        if hasattr(response_msg, 'content') and isinstance(response_msg.content, str):
             raw_response = response_msg.content.strip()
             print(f"---Supervisor Raw Response: '{raw_response}'---")
        else:
             print(f"Warning: Supervisor response unexpected format. Type: {type(response_msg)}, Value: {response_msg}")
             raw_response = "FINISH" # Default to FINISH on unexpected format

        # Check if the raw response is one of the valid options
        if raw_response in options:
            next_worker = raw_response
        else:
            # Fallback if the response is not exactly one of the options
            print(f"Warning: Supervisor response '{raw_response}' not in valid options {options}. Defaulting to FINISH.")
            next_worker = "FINISH"
        print(f"---Supervisor Decision: Route to {next_worker}---")
        if next_worker == "FINISH":
            return Command(goto=END, update={"next": None})
        else:
            # Ensure the chosen worker is actually in the members list before routing
            if next_worker in members:
                return Command(goto=next_worker, update={"next": next_worker})
            else:
                print(f"Error: Supervisor chose invalid worker '{next_worker}'. Defaulting to FINISH.")
                return Command(goto=END, update={"next": None}) # Go to END if invalid worker chosen
    return supervisor_node