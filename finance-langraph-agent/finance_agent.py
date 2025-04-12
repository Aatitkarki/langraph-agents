import json
import os
from typing import List, Dict, Any, Optional

# LangGraph and related imports
from typing_extensions import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
# Assuming we'll use langchain_core tools and potentially an LLM later
from langchain_core.tools import tool 
from langgraph.prebuilt import ToolExecutor
# We might need an LLM later, placeholder import
# from langchain_openai import ChatOpenAI 

# --- Agent State Definition ---
class AgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        query: The initial user query.
        intent: The determined intent (e.g., 'information', 'action', 'clarify', 'error').
        tool_name: The name of the tool selected by the agent.
        tool_input: The input parameters for the selected tool.
        tool_output: The result returned by the tool execution.
        response: The final response string to be shown to the user.
        error: Any error message encountered during processing.
        # Potentially add message history if needed for conversational context
        # messages: Annotated[List[AnyMessage], operator.add] 
    """
    query: str
    intent: Optional[str]
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[Any] 
    response: Optional[str]
    error: Optional[str]


# Define the path to the mock data directory
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
            # Return structure consistent with successful reads but indicate potential issue
            return {"ResponseData": data.get("ResponseData", None), "Error": data.get('ActDescription', 'Failed status in data')}
        return data
    except FileNotFoundError:
        print(f"Error: Mock data file not found at {file_path}")
        return {"ResponseData": None, "Error": f"File not found: {file_path}"}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return {"ResponseData": None, "Error": f"Invalid JSON in file: {file_path}"}
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        return {"ResponseData": None, "Error": f"Unexpected error reading file: {e}"}

# --- Tool Implementations will go here ---

@tool
def get_dashboard_summary() -> Dict[str, Any]:
    """
    Retrieves a summary of the dashboard landing data, including account and card lists.
    """
    data = read_mock_data(DASHBOARD_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}
    
    response_data = data.get("ResponseData", {})
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
        "loans": response_data.get("Loans", []), # Assuming loans structure is simple for now
        "investments": response_data.get("Investments", []) # Assuming investments structure is simple
    }
    return summary

@tool
def get_account_balance(account_no: str) -> Dict[str, Any]:
    """
    Retrieves the available balance for a specific account number.
    Account number should match the 'AccountNo' field (e.g., '4080201040001').
    """
    data = read_mock_data(DASHBOARD_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    response_data = data.get("ResponseData", {})
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
def get_transaction_history(account_no: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Retrieves transaction history. 
    Optionally filters by account number (Note: Mock data doesn't link transactions to accounts, so filtering is illustrative).
    Limits the number of transactions returned.
    """
    data = read_mock_data(TRANSACTIONS_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    transactions = data.get("ResponseData", [])
    
    # Placeholder for account filtering if data structure supported it
    # if account_no:
    #     transactions = [t for t in transactions if t.get("AccountNo") == account_no] 
        
    # Apply limit
    transactions = transactions[:limit]

    if not transactions:
         # Check if the original data was empty or filtering resulted in empty
         if not data.get("ResponseData"):
             return {"message": "No transaction data available."}
         else:
             return {"message": f"No transactions found matching the criteria (Account: {account_no})."}

    return {"transactions": transactions}

@tool
def get_card_details(card_identifier: str) -> Dict[str, Any]:
    """
    Retrieves details for a specific card based on an identifier.
    Identifier can be the last 4 digits of 'CardNo' or the 'CardSerNo'.
    """
    data = read_mock_data(DASHBOARD_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    response_data = data.get("ResponseData", {})
    cards = response_data.get("Cards", [])
    
    for card in cards:
        # Check last 4 digits (assuming format 'XXXX XXXX XXXX 1234')
        last_four = card.get("CardNo", "").split(" ")[-1] 
        if card_identifier == last_four or card.get("CardSerNo") == card_identifier:
            # Return relevant details (adjust as needed)
            return {
                "name_on_card": card.get("NameOnCard"),
                "card_no_masked": card.get("CardNo"),
                "card_serial_no": card.get("CardSerNo"),
                "type": card.get("CardProductType"),
                "status": card.get("Status"),
                "card_limit": card.get("CardLimit"),
                "available_balance": card.get("AvailableBalance"),
                "outstanding_balance": card.get("OutstandindBalance"), # Typo in mock data ('OutstandindBalance')
                "payment_due_date": card.get("PaymentDueDate"),
            }
            
    return {"error": f"Card with identifier '{card_identifier}' not found."}

@tool
def get_exchange_rate(currency_code: str) -> Dict[str, Any]:
    """
    Retrieves the exchange rate for a specific currency code (e.g., 'USD', 'INR').
    """
    data = read_mock_data(EXCHANGE_RATES_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    rates = data.get("ResponseData", [])
    
    for rate_info in rates:
        if rate_info.get("Code", "").upper() == currency_code.upper():
            return {
                "currency_code": rate_info.get("Code"),
                "currency_name": rate_info.get("Name"),
                "rate": rate_info.get("Rate")
            }
            
    return {"error": f"Exchange rate for currency code '{currency_code}' not found."}

@tool
def simulate_cancel_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Simulates cancelling a transaction identified by its ID (DealReference or TransactionSeqNo).
    In a real system, this would trigger an API call. Here, it just logs the attempt.
    """
    data = read_mock_data(TRANSACTIONS_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    transactions = data.get("ResponseData", [])
    
    found = False
    for tx in transactions:
        if tx.get("DealReference") == transaction_id or tx.get("TransactionSeqNo") == transaction_id:
            found = True
            # In a real scenario, you might check if cancellation is allowed
            print(f"--- ACTION SIMULATION: Attempting to cancel transaction {transaction_id} ---")
            # Simulate success
            return {"success": True, "message": f"Transaction {transaction_id} cancellation request submitted."}
            
    if not found:
        return {"success": False, "error": f"Transaction with ID '{transaction_id}' not found for cancellation."}
    
    # Fallback in case logic error occurs (shouldn't happen here)
    return {"success": False, "error": "An unexpected error occurred during cancellation simulation."}


@tool
def simulate_raise_dispute(transaction_id: str, reason: str) -> Dict[str, Any]:
    """
    Simulates raising a dispute for a transaction identified by its ID (DealReference or TransactionSeqNo).
    In a real system, this would trigger an API call. Here, it just logs the attempt.
    """
    data = read_mock_data(TRANSACTIONS_FILE)
    if data.get("Error"):
        return {"error": data["Error"]}

    transactions = data.get("ResponseData", [])
    
    found = False
    for tx in transactions:
         if tx.get("DealReference") == transaction_id or tx.get("TransactionSeqNo") == transaction_id:
            found = True
            # In a real scenario, you might check if the transaction is eligible for dispute (tx.get("IsEligibleForDispute"))
            print(f"--- ACTION SIMULATION: Attempting to raise dispute for transaction {transaction_id} ---")
            print(f"--- Reason: {reason} ---")
            # Simulate success
            return {"success": True, "message": f"Dispute submitted for transaction {transaction_id} with reason: '{reason}'."}

    if not found:
        return {"success": False, "error": f"Transaction with ID '{transaction_id}' not found for raising dispute."}
        
    # Fallback
    return {"success": False, "error": "An unexpected error occurred during dispute simulation."}


# --- Tool Executor Setup ---
tools = [
    get_dashboard_summary,
    get_account_balance,
    get_transaction_history,
    get_card_details,
    get_exchange_rate,
    simulate_cancel_transaction,
    simulate_raise_dispute,
]
tool_executor = ToolExecutor(tools)

# --- Agent Nodes ---

def orchestrator(state: AgentState) -> Dict[str, Any]:
    """
    Determines the intent and selects the appropriate tool or decides to respond directly.
    (Mock implementation - A real implementation would use an LLM)
    """
    print("--- Entering Orchestrator ---")
    query = state['query'].lower().strip()
    
    # --- Handle Meta Queries First ---
    if query in ["help", "what can you do?", "capabilities"]:
        print("Intent: Meta - Capabilities Request")
        capabilities = """
I am a Finance Bank Agent. I can help you with the following financial tasks:
- Get a summary of your dashboard (accounts, cards).
- Check the balance for a specific account.
- View recent transaction history.
- Get details for a specific credit card.
- Find the current exchange rate for a currency.
- Request cancellation of a transaction (simulated).
- Raise a dispute for a transaction (simulated).

Please provide specific details like account numbers, card identifiers (last 4 digits or serial number), transaction IDs, or currency codes when asking questions.
"""
        return {"intent": "clarify", "response": capabilities} # Use clarify intent to send direct response

    # --- Simple keyword-based routing for Finance tasks ---
    if "cancel transaction" in query:
        # Extract transaction ID (very basic parsing)
        parts = query.split()
        tx_id = parts[-1] if len(parts) > 2 else None
        # Basic check if it looks like an ID (contains digits)
        if tx_id and any(char.isdigit() for char in tx_id):
             print(f"Intent: Action - Cancel Transaction (ID: {tx_id})")
             return {"intent": "action", "tool_name": "simulate_cancel_transaction", "tool_input": {"transaction_id": tx_id}}
        else:
             print("Intent: Error - Missing or invalid Transaction ID for cancellation")
             return {"intent": "error", "error": "Please provide a valid transaction ID to cancel."}

    elif "raise dispute" in query or "dispute transaction" in query:
         # Extract transaction ID and reason (very basic parsing)
         parts = query.split()
         tx_id = None
         reason = "No reason provided" # Default reason
         # Look for ID (assuming it's often near the end or after 'transaction')
         for i, part in enumerate(parts):
             # Simple check for potential ID (contains digits, maybe starts with 0)
             if any(char.isdigit() for char in part): 
                 tx_id = part
                 # Try to capture reason after ID
                 if i + 2 < len(parts) and parts[i+1] in ["reason", "for"]:
                     reason = " ".join(parts[i+2:])
                 elif i + 1 < len(parts): # Assume reason follows ID if not explicitly stated
                     reason = " ".join(parts[i+1:])
                 break
         if tx_id:
             print(f"Intent: Action - Raise Dispute (ID: {tx_id}, Reason: {reason})")
             return {"intent": "action", "tool_name": "simulate_raise_dispute", "tool_input": {"transaction_id": tx_id, "reason": reason}}
         else:
             print("Intent: Error - Missing or invalid Transaction ID for dispute")
             return {"intent": "error", "error": "Please provide a valid transaction ID to dispute."}

    elif "balance" in query:
        # Extract account number (very basic parsing - assumes format like 'balance for 40...')
        acc_no = None
        parts = query.split()
        for i, part in enumerate(parts):
            # Simple check for account number format (contains digits, maybe hyphens)
            cleaned_part = part.replace('-', '')
            if cleaned_part.isdigit() and len(cleaned_part) > 5: 
                 acc_no = cleaned_part # Use the internal format
                 break
        if acc_no:
            print(f"Intent: Information - Get Balance (Account: {acc_no})")
            return {"intent": "information", "tool_name": "get_account_balance", "tool_input": {"account_no": acc_no}}
        else:
            # If no specific account, maybe default to summary or ask? For now, assume summary.
            print("Intent: Information - Get Dashboard Summary (Defaulting due to no specific account in balance query)")
            return {"intent": "information", "tool_name": "get_dashboard_summary", "tool_input": {}}

    elif "transaction history" in query or "recent transactions" in query:
        print("Intent: Information - Get Transaction History")
        # Could add logic here to parse account number or limit if specified in query
        return {"intent": "information", "tool_name": "get_transaction_history", "tool_input": {}} # Default limit applies

    elif "card details" in query:
         # Extract card identifier (very basic parsing - assumes last word is identifier)
         parts = query.split()
         card_id = parts[-1] if len(parts) > 2 else None
         # Basic check if it looks like a card identifier (e.g., 4 digits or longer alphanumeric)
         if card_id and (card_id.isdigit() and len(card_id) == 4 or len(card_id) > 4):
             print(f"Intent: Information - Get Card Details (Identifier: {card_id})")
             return {"intent": "information", "tool_name": "get_card_details", "tool_input": {"card_identifier": card_id}}
         else:
             print("Intent: Error - Missing or invalid Card Identifier")
             return {"intent": "error", "error": "Please provide a valid card identifier (last 4 digits or serial number)."}

    elif "exchange rate" in query:
         # Extract currency code (very basic parsing - assumes code follows 'for')
         code = None
         parts = query.split()
         if "for" in parts:
             idx = parts.index("for")
             if idx + 1 < len(parts):
                 code = parts[idx+1].upper()
         if code and len(code) == 3 and code.isalpha(): # Check if it's 3 letters
             print(f"Intent: Information - Get Exchange Rate (Code: {code})")
             return {"intent": "information", "tool_name": "get_exchange_rate", "tool_input": {"currency_code": code}}
         else:
             print("Intent: Error - Missing or invalid Currency Code")
             return {"intent": "error", "error": "Please provide a valid 3-letter currency code (e.g., USD, INR)."}

    elif "summary" in query or "dashboard" in query:
        print("Intent: Information - Get Dashboard Summary")
        return {"intent": "information", "tool_name": "get_dashboard_summary", "tool_input": {}}

    else:
        # --- Non-Finance Check (Basic) ---
        # Add keywords that are clearly out of scope
        non_finance_keywords = ["weather", "news", "recipe", "joke", "translate", "capital of"]
        if any(keyword in query for keyword in non_finance_keywords):
            print("Intent: Out of Scope")
            return {"intent": "clarify", "response": "I am a Finance Bank Agent and can only assist with financial matters related to your accounts, cards, transactions, and exchange rates."}
        else:
            # --- Default Clarification ---
            print("Intent: Unclear / General")
            # Default to a general response or ask for clarification
            return {"intent": "clarify", "response": "I'm sorry, I couldn't understand that request. As a Finance Bank Agent, I can help with account balances, transactions, card details, and exchange rates. Could you please rephrase your financial query?"}


def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    """Executes the selected tool."""
    print(f"--- Executing Tool: {state['tool_name']} ---")
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input", {})
    
    if not tool_name:
        print("Error: No tool name provided for execution.")
        return {"error": "Internal error: Tool name missing.", "tool_output": None}

    # ToolExecutor expects a dict with 'tool_name' and 'tool_input' keys
    # Note: LangChain's ToolExecutor might have slightly different invocation patterns
    # depending on version and specific setup. This assumes a basic direct call.
    # In more complex scenarios (like with LangChain Expression Language), you might structure this differently.
    
    # Find the actual tool function from our list
    selected_tool = None
    for t in tools:
        if t.name == tool_name:
            selected_tool = t
            break
            
    if not selected_tool:
         print(f"Error: Tool '{tool_name}' not found in the tool list.")
         return {"error": f"Internal error: Tool '{tool_name}' not found.", "tool_output": None}

    try:
        # Directly call the tool function with its arguments
        output = selected_tool.invoke(tool_input) 
        print(f"Tool Output: {output}")
        return {"tool_output": output}
    except Exception as e:
        print(f"Error executing tool {tool_name}: {e}")
        # It might be useful to return the specific exception string
        return {"error": f"Error during tool execution: {str(e)}", "tool_output": None}

def generate_response_node(state: AgentState) -> Dict[str, Any]:
    """Generates a final response based on the state."""
    print("--- Generating Response ---")
    if state.get("error"):
        # Prioritize showing errors clearly
        response = f"An error occurred: {state['error']}"
    elif state.get("intent") == "clarify":
        # Handle cases where the orchestrator couldn't understand
        response = state.get("response", "Could you please clarify your request?")
    elif state.get("tool_output") is not None:
        # Format the output from the tool execution
        output = state['tool_output']
        if isinstance(output, dict):
             if output.get("error"):
                 # If the tool itself returned an error message
                 response = f"Error from tool: {output['error']}"
             elif output.get("message"):
                  # If the tool returned a direct message (e.g., action confirmation, no data found)
                 response = output["message"]
             elif output.get("success") is not None: 
                 # Handle structured success/failure from action tools
                 response = output.get("message", "Action completed.") if output["success"] else output.get("error", "Action failed.")
             else:
                 # Generic formatting for other dictionary outputs (like data retrieval)
                 # Pretty print the JSON for readability
                 try:
                     response = f"Here is the information:\n```json\n{json.dumps(output, indent=2)}\n```"
                 except TypeError: # Handle non-serializable data if any
                     response = f"Here is the information: {str(output)}"
        else:
             # Fallback for non-dictionary outputs
             response = str(output) 
    else:
        # Fallback if no error and no tool output (should ideally not happen in normal flow)
        response = "I was unable to process your request or there was no information to return."
        
    print(f"Final Response: {response}")
    return {"response": response}


# --- Conditional Edge Logic ---

def should_continue_edge(state: AgentState) -> str:
    """Determines the next node to route to based on orchestrator's decision."""
    print(f"--- Deciding Next Step (Intent: {state.get('intent')}) ---")
    intent = state.get("intent")
    
    if intent == "error" or intent == "clarify":
        # If orchestrator found an error or needs clarification, go to generate response
        print("Routing: Orchestrator -> Generate Response")
        return "generate_response"
    elif intent == "information" or intent == "action":
        # If a tool is selected, go execute it
        print("Routing: Orchestrator -> Execute Tools")
        return "execute_tools"
    else:
        # If intent is missing or unexpected, end the graph execution
        print("Routing: Orchestrator -> END (Unexpected Intent or End State)")
        return END

# --- Assemble the Graph ---
print("--- Assembling Graph ---")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("orchestrator", orchestrator)
workflow.add_node("execute_tools", execute_tools_node)
workflow.add_node("generate_response", generate_response_node)

# Set entry point
workflow.set_entry_point("orchestrator")

# Add edges
workflow.add_conditional_edges(
    "orchestrator",
    should_continue_edge,
    {
        "execute_tools": "execute_tools",
        "generate_response": "generate_response",
        END: END
    }
)
workflow.add_edge("execute_tools", "generate_response") # Always generate response after executing tools
workflow.add_edge("generate_response", END) # End after generating the response

# Compile the graph
app = workflow.compile()
print("--- Graph Compiled ---")

if __name__ == "__main__":
    print("*"*40)
    print("Welcome! I am your Finance Bank Agent.")
    print("How can I assist you with your finances today?")
    print("*"*40)
    
    # Basic test to ensure data loading works (keep this)
    print("\nTesting data loading...")
    dashboard_data = read_mock_data(DASHBOARD_FILE)
    transactions_data = read_mock_data(TRANSACTIONS_FILE)
    rates_data = read_mock_data(EXCHANGE_RATES_FILE)
    print(f"Dashboard loaded: {'Success' if dashboard_data.get('ResponseData') else 'Failed'}")
    print(f"Transactions loaded: {'Success' if transactions_data.get('ResponseData') else 'Failed'}")
    print(f"Rates loaded: {'Success' if rates_data.get('ResponseData') else 'Failed'}")
    print("-" * 30)

    # --- Test Graph Invocation ---
    print("\n--- Testing Graph Execution ---")

    test_queries = [
        "help", # Test capabilities
        "What is my balance for account 4080201040001?",
        "Show recent transactions",
        "Get card details for 5884", # Last 4 digits
        "Get card details for WMcVYNtwPLE1S2gqK1L9Hg==", # Serial No
        "What is the exchange rate for INR?",
        "Cancel transaction 090325T54843",
        "Dispute transaction 63 because it was wrong",
        "Cancel transaction", # Should trigger orchestrator error
        "What is the weather in Doha?", # Should trigger out-of-scope
        "Tell me a joke", # Should trigger out-of-scope
        "Show dashboard summary",
        "gibberish request" # Should trigger unclear
    ]

    for query in test_queries:
        print(f"\n>>> Testing Query: {query}")
        initial_state = {"query": query}
        
        # Using stream to show the flow (optional, good for debugging)
        print("--- Streaming Events ---")
        final_state_from_stream = None
        for event in app.stream(initial_state):
            for node_name, output in event.items():
                print(f"Output from node: {node_name}")
                # print(f"State Update: {output}") # Can be verbose
                final_state_from_stream = output # Keep track of the last state update
            print("-" * 10)
        print("--- End Stream ---")

        # Get the final response cleanly after streaming
        final_response = final_state_from_stream.get('response', 'No response in final state.') if final_state_from_stream else "Streaming failed to produce final state."
        
        print(f"\n>>> Final Response for '{query}':")
        print(final_response)
        print("=" * 30)

    print("\n--- Graph Testing Complete ---")