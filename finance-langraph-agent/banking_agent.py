import streamlit as st
from openai import OpenAI

import getpass
import os
import uuid
import json
from typing import Annotated, List, Optional, Literal, TypedDict, Dict, Callable

# Langchain Core and Community Imports
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig, Runnable
# from langchain_community.tools.tavily_search import TavilySearchResults # Not used in this finance example
from langchain_experimental.utilities import PythonREPL

# Choose your LLM Provider
# from langchain_openai import ChatOpenAI
from langchain_openai import ChatOpenAI

# Langgraph Imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import SecretStr # Explicitly import Command

# --- Choose and Instantiate LLM ---
# llm = ChatOpenAI(model="gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE","")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")

llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY),
    base_url=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
) 

# --- Mock Data Loading ---
# Assumes JSON files are in a './mock_data/' subdirectory relative to the script
mock_data_dir = "./mock_data"

def load_mock_data(filename: str) -> dict:
    """Loads mock data from a JSON file with basic error handling."""
    filepath = os.path.join(mock_data_dir, filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Mock data file not found: {filepath}. Returning empty data.")
        return {"ResponseData": None} # Return structure expected by tools
    except json.JSONDecodeError as e:
        print(f"Warning: Error decoding JSON from {filepath}. Details: {e}. Returning empty data.")
        return {"ResponseData": None}

# Load all mock data at the start
dashboard_data = load_mock_data("dashboard_landing.json")
transactions_data = load_mock_data("account_transactions.json")
exchange_rates_data = load_mock_data("exchange_rates.json")

# --- Tool Definitions (Using Mock Data) ---

@tool
def get_account_summary() -> List[Dict]:
    """Retrieves the summary of the user's accounts, including balance and type."""
    print("---Tool: get_account_summary called---")
    data = dashboard_data.get("ResponseData", {}).get("Accounts", [])
    if not data:
         return [{"Error": "No account summary data available."}]
    # Optionally filter/simplify the data returned to the agent
    # simplified_data = [{"AccountNo": acc.get("DisplayAccountNo"), "Balance": acc.get("AvailableBalance"), "Type": acc.get("AccountType")} for acc in data]
    # return simplified_data
    return data # Returning full data for now

@tool
def get_transactions(account_number: Annotated[Optional[str], "Optional account number to filter transactions."],
                     limit: Annotated[Optional[int], "Optional limit on the number of transactions to return."]) -> List[Dict]:
    """
    Retrieves the transaction history for the user's account.
    Optionally filters by account number (mock ignores this) and limits the number of results.
    """
    print(f"---Tool: get_transactions called (Account: {account_number}, Limit: {limit})---")
    data = transactions_data.get("ResponseData", [])
    if not data:
         return [{"Error": "No transaction data available."}]
    if limit:
        return data[:limit]
    return data

@tool
def get_credit_card_details() -> List[Dict]:
    """Retrieves details about the user's credit cards, including limits, balances, and due dates."""
    print("---Tool: get_credit_card_details called---")
    data = dashboard_data.get("ResponseData", {}).get("Cards", [])
    if not data:
         return [{"Error": "No credit card data available."}]
    return data

@tool
def get_exchange_rates(currency_codes: Annotated[Optional[List[str]], "Optional list of currency codes (e.g., ['USD', 'EUR']) to retrieve rates for."]) -> List[Dict]:
    """
    Retrieves foreign exchange rates relative to QAR.
    If no codes are provided, returns all available rates.
    Each rate indicates how many QAR 1 unit of the foreign currency is worth (e.g., {'Code': 'USD', 'Rate': 3.65} means 1 USD = 3.65 QAR).
    """
    print(f"---Tool: get_exchange_rates called (Codes: {currency_codes})---")
    all_rates = exchange_rates_data.get("ResponseData", [])
    if not all_rates:
        return [{"Error": "Exchange rate data not available."}]

    if not currency_codes:
        # Return all rates if no specific codes are requested
        return all_rates
    else:
        # Filter for requested codes
        requested_rates = []
        code_map = {rate['Code'].upper(): rate for rate in all_rates}
        codes_to_check = [code.upper() for code in currency_codes]
        for code in codes_to_check:
            if code in code_map:
                requested_rates.append(code_map[code])
            else:
                requested_rates.append({"Code": code, "Error": "Rate not found"})
        return requested_rates

# Python REPL Tool (for calculations like currency conversion)
repl = PythonREPL()
@tool
def python_repl_tool_finance(
    code: Annotated[str, "The python code to execute for calculations like currency conversion."],
):
    """Use this to execute python code for financial calculations.
       Make sure to use the provided exchange rates.
       If you want to see the output of a value, print it out with `print(...)`.
       This is visible to the user. Wrap the final result in the print() statement.
    """
    print(f"---Tool: python_repl_tool_finance executing code:\n{code}\n---")
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute code. Error: {repr(e)}"
    return f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"


# --- Shared State Definition ---
class FinancialAgentState(MessagesState):
   # MessagesState stores the list of messages
   next: Optional[str] # Stores the name of the next agent to route to

# --- Helper Functions ---

def create_supervisor_finance(llm: BaseChatModel, members: list[str]):
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
        "Respond ONLY with the name of the next specialist agent ('account_agent', 'transaction_agent', 'card_agent', 'exchange_rate_agent') or 'FINISH'."
        "Do not add any other explanation to your final output."
    )

    # Also update the Router Literal to match the exact agent names if needed (they seem correct)
    # class Router(BaseModel):
    #     """Select the next specialist agent or FINISH."""
    #     next: Literal["FINISH", "account_agent", "transaction_agent", "card_agent", "exchange_rate_agent"]

    from pydantic import BaseModel
    class Router(BaseModel):
        """Select the next specialist agent or FINISH."""
        next: Literal["FINISH", "account_agent", "transaction_agent", "card_agent", "exchange_rate_agent"]

    supervisor_chain = llm.with_structured_output(Router, include_raw=False)

    def supervisor_node(state: FinancialAgentState) -> Command[str]:
        """Routes work to the appropriate worker or finishes."""
        print("---Supervisor Running---")
        last_message = state['messages'][-1]
        # Supervisor decides based on the conversation history
        # Filter out tool messages for brevity if needed for the supervisor LLM call
        supervisor_input_messages = [m for m in state['messages'] if not isinstance(m, ToolMessage)]
        supervisor_input_messages = [HumanMessage(content=system_prompt)] + supervisor_input_messages

        response = supervisor_chain.invoke(supervisor_input_messages)

        # Explicitly check the type before accessing the attribute
        if isinstance(response, Router):
            next_worker = response.next
        else:
            # Fallback if the response is not the expected Pydantic model
            # This path is less likely with include_raw=False, but adds robustness
            print(f"Warning: Supervisor response type unexpected. Type: {type(response)}, Value: {response}")
            # Attempt dictionary access or default to FINISH
            try:
                next_worker = response.get("next", "FINISH") if isinstance(response, dict) else "FINISH"
            except Exception:
                 print("Error: Could not determine next worker from supervisor response.")
                 next_worker = "FINISH" # Default to FINISH on error
        print(f"---Supervisor Decision: Route to {next_worker}---")
        if next_worker == "FINISH":
            return Command(goto=END, update={"next": None})
        else:
            return Command(goto=next_worker, update={"next": next_worker})
    return supervisor_node

def create_worker_node_finance(agent_name: str, agent: Runnable): # Agent is a Runnable (CompiledGraph)
    """Creates a worker node that invokes the agent and prepares the output."""
    def worker_node(state: FinancialAgentState) -> Dict[str, List[BaseMessage]]:
        print(f"---Worker Node: {agent_name} Running---")
        result = agent.invoke(state)
        # Wrap the final response in a HumanMessage with the agent's name
        # This helps the supervisor know who last spoke. Check for AIMessage type first.
        last_agent_message = result["messages"][-1]
        content_to_format = ""
        if isinstance(last_agent_message, AIMessage):
             content_to_format = last_agent_message.content
        elif isinstance(last_agent_message, (HumanMessage, ToolMessage)): # Handle cases where agent might return tool/human msg last
             content_to_format = last_agent_message.content
        else:
             content_to_format = str(last_agent_message) # Fallback

        formatted_message = HumanMessage(
            content=content_to_format, name=agent_name, id=str(uuid.uuid4())
        )
        print(f"---Worker Node: {agent_name} Finished---")
        return {"messages": [formatted_message]}
        # Worker returns its output; supervisor decides the next step based on this.
        # No need for the worker to determine goto or check for "FINAL ANSWER" itself.
    return worker_node

def finance_agent_system_prompt(task_description: str) -> str:
    """Creates a standardized system prompt for the financial agents."""
    return (
        "You are a specialized financial assistant collaborating with other agents under a supervisor.\n"
        f"Your specific task is: {task_description}\n"
        "Use your assigned tools ONLY to fulfill the request related to your specific task.\n"
        "If you can fully address the relevant part of the user's query, provide the answer concisely.\n"
        "If the request requires capabilities or tools you don't have (e.g., needing account balance when you only handle transactions, or needing currency conversion when you only handle accounts), "
        "state that you have completed your part and indicate what information is still needed or which specialist might be required next.\n"
        "Do not ask follow-up questions to the user. Only use your tools based on the existing request.\n"
        "If you have successfully completed your part of the task or the entire request, conclude your response clearly."
        # Adding "FINISH" signal explicitly might confuse supervisor if used prematurely by worker.
        # Rely on supervisor to determine overall completion.
    )

# --- Agent Definitions ---

print("--- Defining Finance Agents ---")
# 1. Account Information Agent
account_agent = create_react_agent(
    llm,
    tools=[get_account_summary],
    prompt=finance_agent_system_prompt("Retrieve and report account summary information like balance, account number, and type based on the user's request.")
)

# 2. Transaction History Agent
transaction_agent = create_react_agent(
    llm,
    tools=[get_transactions],
    prompt=finance_agent_system_prompt("Retrieve and report transaction history for user accounts based on the user's request (e.g., last N transactions, specific date range - though mock data is limited).")
)

# 3. Credit Card Agent
card_agent = create_react_agent(
    llm,
    tools=[get_credit_card_details],
    prompt=finance_agent_system_prompt("Retrieve and report credit card details like balance, limit, and due dates based on the user's request.")
)

# 4. Exchange Rate & Calculation Agent
exchange_rate_agent = create_react_agent(
    llm,
    tools=[get_exchange_rates, python_repl_tool_finance],
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

# --- Node Definitions ---
print("--- Defining Graph Nodes ---")
supervisor_node_finance = create_supervisor_finance(llm, ["account_agent", "transaction_agent", "card_agent", "exchange_rate_agent"])
account_node_finance = create_worker_node_finance("account_agent", account_agent)
transaction_node_finance = create_worker_node_finance("transaction_agent", transaction_agent)
card_node_finance = create_worker_node_finance("card_agent", card_agent)
exchange_rate_node_finance = create_worker_node_finance("exchange_rate_agent", exchange_rate_agent)

# --- Graph Definition ---
print("--- Building Finance Agent Graph ---")
finance_builder = StateGraph(FinancialAgentState)

finance_builder.add_node("supervisor", supervisor_node_finance)
finance_builder.add_node("account_agent", account_node_finance)
finance_builder.add_node("transaction_agent", transaction_node_finance)
finance_builder.add_node("card_agent", card_node_finance)
finance_builder.add_node("exchange_rate_agent", exchange_rate_node_finance)

# Edges: Start goes to supervisor, workers go back to supervisor
finance_builder.add_edge(START, "supervisor")
finance_builder.add_edge("account_agent", "supervisor")
finance_builder.add_edge("transaction_agent", "supervisor")
finance_builder.add_edge("card_agent", "supervisor")
finance_builder.add_edge("exchange_rate_agent", "supervisor")

# Compile the graph with memory
memory = InMemorySaver()
finance_graph = finance_builder.compile(checkpointer=memory)

print("--- Finance Agent Graph Compiled Successfully! ---")

# --- Example Invocations ---

def run_finance_query(query: str, thread_id: str, openai_api_key: Optional[str] = None): # Make key optional for flexibility
    """Runs a query through the finance graph and prints the final response."""
    print(f"\n--- [run_finance_query] START ---")
    print(f"Query: '{query}'")
    print(f"Thread ID: {thread_id}")
    print(f"API Key Provided: {'Yes' if openai_api_key else 'No'}") # Don't print the key itself

    # Note: The global `llm` instance uses env vars by default.
    # If an API key is provided here, the current setup DOES NOT automatically use it
    # for the agents created outside this function. This might be the core issue.
    # For now, let's focus on tracing the execution.

    config = RunnableConfig({"configurable": {"thread_id": thread_id}})
    final_state = None
    print(f"--- [run_finance_query] Invoking finance_graph... ---")
    try:
        final_state = finance_graph.invoke(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )
        print(f"--- [run_finance_query] Invocation finished. ---")
        print(f"Final State: {final_state}") # Print the whole state for debugging
    except Exception as e:
        print(f"--- [run_finance_query] ERROR during graph invocation: {e} ---")
        import traceback
        traceback.print_exc() # Print full traceback
        return f"Error during agent execution: {e}"

    # Print the stream of events for detailed tracing (optional)
    # print("\n--- Event Stream ---")
    # for event in finance_graph.stream({"messages": [HumanMessage(content=query)]}, config=config):
    #      for key, value in event.items():
    #         print(f"Output from node '{key}':")
    #         print("---")
    #         print(value)
    #      print("\n---\n")

    # Process final response
    if final_state and isinstance(final_state, dict) and final_state.get('messages'):
        try:
            # Get the last message, which should be from the agent or supervisor
            last_msg = final_state['messages'][-1]
            print(f"--- [run_finance_query] Last message object: {last_msg} ---")

            # Extract content based on message type
            if isinstance(last_msg, AIMessage):
                response_content = last_msg.content
            elif isinstance(last_msg, HumanMessage):
                 # If the last message was the formatted one from a worker node
                 response_content = last_msg.content
            elif isinstance(last_msg, ToolMessage):
                 response_content = f"Tool execution result: {last_msg.content}" # Less ideal, supervisor should respond
            elif hasattr(last_msg, 'content'):
                 response_content = last_msg.content # General fallback
            else:
                 response_content = str(last_msg) # Raw fallback

            print(f"--- [run_finance_query] Extracted response: {response_content} ---")
            print(f"--- [run_finance_query] END ---")
            return response_content
        except Exception as e:
            print(f"--- [run_finance_query] ERROR processing final state: {e} ---")
            return f"Error processing agent response: {e}"
    else:
        print(f"--- [run_finance_query] No final state or messages found. ---")
        print(f"--- [run_finance_query] END ---")
        return "Agent did not produce a final response."
    
# Removed Streamlit chat input block - this logic is now in streamlit_app.py

# --- Run Example Queries ---
# The following example queries are commented out to ensure the Streamlit app is the only thing running.
# run_finance_query("What is the available balance in my current account?", "finance_thread_1_final")
# run_finance_query("Show me my last transaction.", "finance_thread_2_final")
# run_finance_query("What's the limit on my Visa Platinum card and its payment due date?", "finance_thread_3_final")
# run_finance_query("What is the exchange rate for USD to QAR?", "finance_thread_4_final")
# run_finance_query("How much is 100 GBP in QAR?", "finance_thread_5_final")
# run_finance_query("How much is 487.47 QAR in INR?", "finance_thread_5_final")
# run_finance_query("How much is 100 GBP in INR?", "finance_thread_7_final") # Multi-step conversion
# run_finance_query("Tell me my account balance and my Visa Platinum card outstanding balance.", "finance_thread_6_final") # Requires multiple agents
