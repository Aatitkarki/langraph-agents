import json
import os
from typing import List, Dict, Any, Optional, Annotated, Union
import operator

# --- Environment Setup ---
# Make sure to create a .env file with your OPENAI_API_KEY
# or set it as an environment variable.
from dotenv import load_dotenv
load_dotenv() 

# --- Langchain / LangGraph Imports ---
from pydantic import SecretStr
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.runnables import RunnableLambda
# Use ChatOpenAI for OpenAI or compatible APIs
from langchain_openai import ChatOpenAI 

# --- Agent State Definition ---
# We'll primarily use messages to pass information.
# Other fields can be added if needed for specific tracking.
class AgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        messages: The list of messages exchanged between the user and the agent.
                  This is the primary way state is passed and managed.
    """
    messages: Annotated[List[BaseMessage], operator.add]

# --- LLM Initialization ---
# Replace with your model details if not using default OpenAI
# Ensure OPENAI_API_KEY is set in your environment or .env file
# You might need to add base_url and api_key for compatible APIs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE","")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")

llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY),
    base_url=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
) 

# --- Mock Data Setup ---
MOCK_DATA_DIR = "mock_data"
DASHBOARD_FILE = os.path.join(MOCK_DATA_DIR, "dashboard_landing.json")
TRANSACTIONS_FILE = os.path.join(MOCK_DATA_DIR, "account_transactions.json")
EXCHANGE_RATES_FILE = os.path.join(MOCK_DATA_DIR, "exchange_rates.json")

def read_mock_data(file_path: str) -> Dict[str, Any]:
    """Helper function to read JSON data from mock files."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        if not data.get("IsSucceeded", False):
            print(f"Warning: Data source reported failure for {file_path}: {data.get('ActDescription', 'Unknown error')}")
            return {"ResponseData": data.get("ResponseData", None), "Error": data.get('ActDescription', 'Failed status in data')}
        # Return only the core data if successful
        return data.get("ResponseData", {}) 
    except FileNotFoundError:
        print(f"Error: Mock data file not found at {file_path}")
        return {"Error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return {"Error": f"Invalid JSON in file: {file_path}"}
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        return {"Error": f"Unexpected error reading file: {e}"}
        return {"Error": f"Unexpected error reading file: {e}"}

# --- Tool Implementations ---
# Tools now return the data directly or an error dict

@tool
def get_dashboard_summary() -> Dict[str, Any]:
    """
    Retrieves a summary of the dashboard landing data, including account and card lists. 
    Use this for general overview requests when no specific account or card is mentioned.
    """
    response_data = read_mock_data(DASHBOARD_FILE)
    if response_data.get("Error"):
        return {"error": response_data["Error"]}
    
    summary = {
        "accounts": [
            {
                "account_no": acc.get("DisplayAccountNo"),
                "type": acc.get("AccountType"),
                "balance": acc.get("AvailableBalance"),
                "currency": acc.get("CurrencyCode")
            } for acc in response_data.get("Accounts", [])
        ],
        "cards": [
            {
                "card_no_masked": card.get("CardNo"),
                "type": card.get("CardProductType"),
                "status": card.get("Status"),
                "available_balance": card.get("AvailableBalance")
            } for card in response_data.get("Cards", [])
        ],
        "loans_count": len(response_data.get("Loans", [])), 
        "investments_count": len(response_data.get("Investments", [])) 
    }
    return summary

@tool
def get_account_balance(account_no: str) -> Dict[str, Any]:
    """
    Retrieves the available balance for a specific account number.
    The account number should be the internal number like '4080201040001'.
    """
    response_data = read_mock_data(DASHBOARD_FILE)
    if response_data.get("Error"):
        return {"error": response_data["Error"]}

    accounts = response_data.get("Accounts", [])
    for account in accounts:
        if account.get("AccountNo") == account_no:
            return {
                "account_no": account.get("DisplayAccountNo"),
                "available_balance": account.get("AvailableBalance"),
                "currency": account.get("CurrencyCode")
            }
    return {"error": f"Account number '{account_no}' not found."}

@tool
def get_transaction_history(account_no: Optional[str], limit: Optional[int]) -> Union[Dict[str, Any], str]:
    """
    Retrieves recent transaction history. 
    Optionally filters by account number (NOTE: Mock data currently doesn't support filtering by account_no, so providing it won't filter results).
    Returns the latest transactions up to the specified limit (defaults to 5 if not provided).
    """
    response_data = read_mock_data(TRANSACTIONS_FILE)
    # If read_mock_data returned an error, return empty list
    if response_data.get("Error"):
         print(f"Error reading transaction data: {response_data['Error']}")
         return "Transaction history data is currently unavailable due to a data source error."

    # Set default limit if not provided by LLM
    effective_limit = limit if limit is not None else 5

    # Attempt to slice first, assuming it's a list. Handle TypeError if not.
    try:
        # Apply limit (to the latest transactions assuming list is ordered reverse-chronologically)
        # Extract the actual list from the 'ResponseData' key
        actual_data = response_data.get("ResponseData", [])
        if not isinstance(actual_data, list):
             raise TypeError(f"Expected list in ResponseData, got {type(actual_data)}")
        limited_transactions = actual_data[:effective_limit]
        # Verify that the result of slicing is indeed a list (it should be)
        if not isinstance(limited_transactions, list):
             # This case is unlikely if the slice succeeded but good for robustness
             raise TypeError("Sliced data is not a list.")
             
    except TypeError:
         # Return message if data is invalid format after extraction attempt
         print(f"Error: Expected list for transaction data, got {type(actual_data)}")
         # Return empty list if data is invalid format after extraction attempt
         return {"transactions": []}
    except Exception as e:
         # Catch other potential errors during processing
         print(f"Error processing transaction data: {e}")
         # Return empty list on error
         # Return message on other errors
         # Return empty list on other errors
         return {"transactions": []}

    # Check if the list is empty after potential slicing
    if not limited_transactions:
         # Return message if no transactions found after filtering/limiting
         return "No recent transaction data found."
         
    # Simplify output for LLM
    formatted_transactions = []
    for tx in limited_transactions:
        if isinstance(tx, dict): # Add explicit check here
            formatted_transactions.append({
                "date": tx.get("TransactionDate", "N/A")[:10], # Just date part
                "description": tx.get("Description", "N/A"),
                "amount": tx.get("DbAmount") if tx.get("Drcr") == "D" else tx.get("CrAmount"),
                "currency": tx.get("Currency", "N/A"),
                "type": tx.get("Drcr", "N/A"), # Debit 'D' or Credit 'C'
                "id": tx.get("DealReference") or tx.get("TransactionSeqNo") # Provide an ID for reference
            })
        else:
            # Handle unexpected item type if necessary, e.g., log a warning
             print(f"Warning: Skipping unexpected item type in transactions list: {type(tx)}")

    # Return the successfully formatted transactions
    return {"transactions": formatted_transactions}
    return {"transactions": formatted_transactions}

@tool
def get_card_details(card_identifier: str) -> Dict[str, Any]:
    """
    Retrieves details for a specific card based on an identifier.
    The identifier should be the last 4 digits of the card number (e.g., '5884') or the full Card Serial Number (e.g., 'WMcVYNtwPLE1S2gqK1L9Hg==').
    """
    response_data = read_mock_data(DASHBOARD_FILE)
    if response_data.get("Error"):
        return {"error": response_data["Error"]}

    cards = response_data.get("Cards", [])
    for card in cards:
        last_four = card.get("CardNo", "").split(" ")[-1]
        if card_identifier == last_four or card.get("CardSerNo") == card_identifier:
            return {
                "name_on_card": card.get("NameOnCard"),
                "card_no_masked": card.get("CardNo"),
                "type": card.get("CardProductType"),
                "status": card.get("Status"),
                "card_limit": card.get("CardLimit"),
                "available_balance": card.get("AvailableBalance"),
                "outstanding_balance": card.get("OutstandindBalance"), 
                "payment_due_date": card.get("PaymentDueDate"),
            }
    return {"error": f"Card with identifier '{card_identifier}' not found."}

@tool
def get_exchange_rate(currency_code: str) -> Union[Dict[str, Any], str]:
    """
    Retrieves the exchange rate for a specific 3-letter currency code (e.g., 'USD', 'INR').
    """
    response_data = read_mock_data(EXCHANGE_RATES_FILE)
    # If read_mock_data returned an error, return unavailable message
    if response_data.get("Error"):
        print(f"Error reading exchange rate data: {response_data['Error']}")
        # Return string message on error
        return "Exchange rate data is currently unavailable due to a data source error."
    # Extract the actual list from the 'ResponseData' key
    rates = response_data.get("ResponseData", [])
    if not isinstance(rates, list):
        # Provide a clearer message for the LLM
        # Return string message on error
        return "Could not process exchange rate data due to unexpected format."
    for rate_info in rates:
        # Ensure rate_info is a dictionary before using .get
        if isinstance(rate_info, dict) and rate_info.get("Code", "").upper() == currency_code.upper():
            return {
                "currency_code": rate_info.get("Code"),
                "currency_name": rate_info.get("Name"),
                "rate_to_QAR": rate_info.get("Rate") # Assuming rate is vs QAR based on context
            }
    # Return unavailable message if currency code not found in the loop
    # Return string message if currency code not found in the loop
    return f"Exchange rate not available for the specified currency '{currency_code}'."

@tool
def simulate_cancel_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Simulates cancelling a transaction identified by its ID (DealReference or TransactionSeqNo).
    Provide the exact transaction ID. This action cannot be undone.
    """
    # In a real system, this would make an API call. Here, we just log and return success.
    # We don't need to read the file for simulation.
    print(f"--- ACTION SIMULATION: Attempting to cancel transaction {transaction_id} ---")
    # Basic validation of ID format might be useful
    if not transaction_id or len(transaction_id) < 5: # Arbitrary basic check
         return {"success": False, "error": f"Invalid transaction ID format provided: '{transaction_id}'."}
    return {"success": True, "message": f"Transaction {transaction_id} cancellation request submitted successfully."}

@tool
def simulate_raise_dispute(transaction_id: str, reason: str) -> Dict[str, Any]:
    """
    Simulates raising a dispute for a specific transaction identified by its ID (DealReference or TransactionSeqNo).
    Provide the exact transaction ID and a brief reason for the dispute.
    """
    # In a real system, this would make an API call.
    print(f"--- ACTION SIMULATION: Attempting to raise dispute for transaction {transaction_id} ---")
    print(f"--- Reason: {reason} ---")
    if not transaction_id or len(transaction_id) < 5: # Arbitrary basic check
         # Make error clearer for LLM
         return {"success": False, "error": f"Tool validation failed: Invalid transaction ID format provided ('{transaction_id}'). Please provide a valid ID."}
    if not reason or len(reason) < 5:
         return {"success": False, "error": "A valid reason must be provided for the dispute."}
    return {"success": True, "message": f"Dispute submitted for transaction {transaction_id} with reason: '{reason}'. A case number will be assigned shortly."}

# --- Tool Executor Setup ---
# The tools list now contains the decorated functions
tools = [
    get_dashboard_summary,
    get_account_balance,
    get_transaction_history,
    get_card_details,
    get_exchange_rate,
    simulate_cancel_transaction,
    simulate_raise_dispute,
]
# Bind the tools to the LLM for the supervisor node
# The supervisor LLM will generate ToolCall messages when it decides to use a tool.
llm_with_tools = llm.bind_tools(tools)
# --- Tool Error Handling ---
def handle_tool_error(state: AgentState) -> dict:
    """Handles errors during tool execution by returning a ToolMessage."""
    error = state.get("error")
    last_message = state["messages"][-1]
    # Ensure the last message is an AIMessage and has tool_calls
    tool_calls = []
    if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', None):
        tool_calls = last_message.tool_calls

    # If there are tool calls, attribute error to them. Otherwise, return a general error message.
    if tool_calls:
        return {
            "messages": [
                ToolMessage(
                    content=f"Error executing tool: {repr(error)}\nPlease review your input and try again.",
                    tool_call_id=tc["id"],
                )
                for tc in tool_calls
            ]
        }
    else:
        # No tool calls associated with the error, return a general error message
        return {
            "messages": [
                AIMessage(content=f"An error occurred: {repr(error)}")
            ]
        }

# --- Tool Executor Setup ---
# Bind the tools to the LLM for the supervisor node
# The supervisor LLM will generate ToolCall messages when it decides to use a tool.
llm_with_tools = llm.bind_tools(tools)
# Create the ToolNode that will execute the tools when called by the graph
# Add fallback for error handling
tool_node = ToolNode(tools).with_fallbacks(
    [RunnableLambda(handle_tool_error)], exception_key="error"
)

# --- Agent Nodes ---

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    This node acts as the supervisor. It calls the LLM to decide what to do next.
    Based on the LLM response, it can either route to the tool executor or end the interaction.
    If a tool returns a string, it means the tool encountered a problem and the string contains a message to relay to the user.
    """
    print("--- Entering Supervisor Node ---")
    # Call the LLM with the current conversation history
    # The LLM decides whether to call a tool or respond directly to the user.
    response = llm_with_tools.invoke(state["messages"])
    print(f"Supervisor LLM Response: {response}")
    # The response from the LLM (which is an AIMessage) is added to the state.
    # If it contains tool_calls, the conditional edge will route to the tool executor.
    # Otherwise, it's considered the final response, and the graph will end.
    return {"messages": [response]}

# We no longer need a custom execute_tools_node, ToolNode handles this.

# --- Conditional Edge Logic ---

def should_continue_edge(state: AgentState) -> str:
    """
    Determines the next step based on the last message.
    If the LLM made tool calls, route to the tool executor. Otherwise, end.
    """
    print("--- Deciding Next Step ---")
    last_message = state["messages"][-1]
    # Check if the last message is an AIMessage and if it has tool_calls attribute and it's not empty/None
    if isinstance(last_message, AIMessage) and getattr(last_message, 'tool_calls', None):
        print("Routing: Supervisor -> ToolNode") # Route to the ToolNode
        return "execute_tools" # The name we gave the ToolNode in the graph
    else:
        print("Routing: Supervisor -> END (LLM provided final response or error)")
        return END

# --- Assemble the Graph ---
print("--- Assembling Graph ---")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
# Use the prebuilt ToolNode instance directly, naming it "execute_tools" in the graph
workflow.add_node("execute_tools", tool_node)

# Set entry point
workflow.set_entry_point("supervisor")

# Add edges
workflow.add_conditional_edges(
    "supervisor",
    should_continue_edge,
    {
        "execute_tools": "execute_tools",
        END: END
    }
)
# After tools are executed, loop back to the supervisor to decide the next step
workflow.add_edge("execute_tools", "supervisor") 

# Compile the graph
# Add checkpointer for memory (optional but good for multi-turn)
# from langgraph.checkpoint.sqlite import SqliteSaver
# memory = SqliteSaver.from_conn_string(":memory:")
# app = workflow.compile(checkpointer=memory)
app = workflow.compile() # Compile without memory for now

print("--- Graph Compiled ---")


if __name__ == "__main__":
    print("*"*40)
    print("Welcome! I am your Commercial Bank Agent.")
    print("How can I assist you with your finances today?")
    print("*"*40)
    
    # Basic test to ensure data loading works (keep this)
    print("\nTesting data loading...")
    dashboard_data = read_mock_data(DASHBOARD_FILE)
    transactions_data = read_mock_data(TRANSACTIONS_FILE) # Note: read_mock_data now returns {} or {"Error":...}
    rates_data = read_mock_data(EXCHANGE_RATES_FILE)

    # Check if the returned value is a dictionary containing an 'Error' key
    print(f"Dashboard loaded: {'Success' if not (isinstance(dashboard_data, dict) and 'Error' in dashboard_data) else 'Failed'}")
    print(f"Transactions loaded: {'Success' if not (isinstance(transactions_data, dict) and 'Error' in transactions_data) else 'Failed'}")
    print(f"Rates loaded: {'Success' if not (isinstance(rates_data, dict) and 'Error' in rates_data) else 'Failed'}")
    print("-" * 30)

    # --- Test Graph Invocation ---
    print("\n--- Testing Graph Execution ---")

    test_queries = [
        "Hi there!",
        "What can you do?", 
        "What is my balance for account 4080201040001?",
        "Show recent transactions",
        "Get card details for 5884", 
        "What is the exchange rate for INR?",
        "Cancel transaction 090325T54843",
        "Dispute transaction 63 because it was wrong",
        "What is the weather in Doha?", 
        "Show dashboard summary"
    ]

    # Example of running with conversation history (if using checkpointer)
    # config = {"configurable": {"thread_id": "user-123"}} 

    for query in test_queries:
        print(f"\n>>> Testing Query: {query}")
        # Initial state now just contains the user message
        initial_state = {"messages": [HumanMessage(content=query)]}
        
        final_state = None
        print("--- Invoking App ---")
        # Use invoke for single-turn testing, stream for seeing steps
        try:
             # Use invoke for simplicity here, stream is better for debugging complex flows
             final_state = app.invoke(initial_state) #, config=config) 
             
             # Extract the last message as the response
             if final_state and final_state.get("messages"):
                 final_response_message = final_state["messages"][-1]
                 # Check if the last message is from the AI and not a ToolMessage
                 if isinstance(final_response_message, AIMessage):
                     final_response = final_response_message.content
                 elif isinstance(final_response_message, ToolMessage):
                     # If the last message was a tool message, something might be off
                     # or the LLM didn't generate a final response after the tool call.
                     # Look for the last AIMessage instead.
                     final_response = "Tool executed. Looking for final AI response..."
                     for msg in reversed(final_state["messages"][:-1]):
                         if isinstance(msg, AIMessage):
                             final_response = msg.content
                             break
                 else:
                     final_response = f"Unexpected final message type: {type(final_response_message)}"
             else:
                 final_response = "No messages found in final state."

        except Exception as e:
            print(f"!!! Error invoking graph: {e}")
            final_response = f"Error during execution: {e}"

        print(f"\n>>> Final Response for '{query}':")
        print(final_response)
        print("=" * 30)

    print("\n--- Graph Testing Complete ---")