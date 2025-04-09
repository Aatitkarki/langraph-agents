# langgraph_usecases/personalized_trip_planner.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.base import BaseCheckpointSaver # Needed for checkpointer type hint
from langgraph.store.base import BaseStore # Needed for store type hint
from langchain_core.runnables import RunnableConfig # Needed for config type hint
import uuid # For generating unique IDs if needed for store keys

# --- State Definition ---
class UserPreferences(TypedDict):
    """Stores user's travel preferences."""
    budget: Optional[str] # e.g., "budget", "mid-range", "luxury"
    interests: List[str] # e.g., ["beach", "history", "food"]
    preferred_airline: Optional[str]

class TripPlan(TypedDict):
    """Represents the current state of the trip plan."""
    destination: Optional[str]
    duration_days: Optional[int]
    flight_info: Optional[str]
    hotel_info: Optional[str]
    activities: List[str]

class PlannerState(TypedDict):
    """Overall state for the personalized trip planner."""
    user_id: str # To identify the user for preference storage/retrieval
    query: str # The user's current request
    preferences: Optional[UserPreferences] # Loaded user preferences
    current_plan: TripPlan
    messages: Annotated[List[BaseMessage], add_messages] # Conversation history

# --- Placeholder Models/Tools ---
# planner_model = ChatOpenAI(model="gpt-4o")
# preference_update_model = ChatOpenAI(model="gpt-4o-mini") # For extracting preferences
@tool
def search_flights(departure: str, destination: str, date: str):
    """Searches for flight options."""
    print(f"---TOOL: Searching flights from {departure} to {destination} on {date}---")
    # Placeholder: Simulate API call
    return f"Flight found: AA123 {departure}-{destination} on {date} for $450."

@tool
def search_hotels(location: str, nights: int):
    """Searches for hotel options."""
    print(f"---TOOL: Searching hotels in {location} for {nights} nights---")
    # Placeholder: Simulate API call
    return f"Hotel found: Grand Hyatt {location}, {nights} nights, $200/night."

TOOLS = [search_flights, search_hotels]
TOOL_MAP = {t.name: t for t in TOOLS}
# model_with_tools = planner_model.bind_tools(TOOLS)

# --- Node Functions ---

def load_or_request_preferences(state: PlannerState, config: RunnableConfig, store: BaseStore) -> dict:
    """Loads preferences from store or asks user if none exist."""
    print("---PLANNER: Loading/Requesting Preferences---")
    user_id = state['user_id']
    namespace = ("preferences", user_id)

    # Try to load preferences from the store
    stored_prefs_items = store.search(namespace, limit=1) # Get the latest preference set

    if stored_prefs_items:
        preferences = stored_prefs_items[0].value # Assuming value is the UserPreferences dict
        print(f"Loaded preferences for user {user_id}: {preferences}")
        return {"preferences": preferences}
    else:
        print(f"No preferences found for user {user_id}. Asking user.")
        # Placeholder: Ask user for preferences (could use interrupt or specific LLM call)
        # For simplicity, assume we get some defaults or ask in the next step
        # This could also trigger an LLM call to formulate the question based on the query
        ask_prefs_msg = AIMessage(content="I don't have your preferences saved. Could you tell me about your budget, interests (e.g., beach, history, food), and preferred airline?")
        # In a real flow, you might interrupt here or have another node handle the response
        return {"messages": [ask_prefs_msg], "preferences": {}} # Return empty prefs for now

def update_preferences_in_store(state: PlannerState, config: RunnableConfig, store: BaseStore) -> dict:
    """Updates preferences in the store based on conversation."""
    print("---PLANNER: Updating Preferences in Store---")
    user_id = state['user_id']
    messages = state['messages']
    current_prefs = state.get('preferences', {})
    namespace = ("preferences", user_id)

    # Placeholder: Use LLM to extract preferences from the latest messages
    # extracted_prefs = preference_update_model.invoke(...)
    # Simple check for demo:
    new_prefs = current_prefs.copy()
    last_user_msg = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if last_user_msg:
        if "budget" in last_user_msg.content.lower():
            new_prefs['budget'] = "budget" # Simplified extraction
        if "beach" in last_user_msg.content.lower():
            interests = new_prefs.get('interests', [])
            if "beach" not in interests: interests.append("beach")
            new_prefs['interests'] = interests

    if new_prefs != current_prefs:
        print(f"Updating preferences for user {user_id}: {new_prefs}")
        # Use a consistent key or generate UUIDs; using a single key 'latest' for simplicity
        store.put(namespace, "latest", new_prefs)
        return {"preferences": new_prefs}
    else:
        print("No preference updates detected.")
        return {}


def plan_trip_step(state: PlannerState) -> dict:
    """Generates the next step of the trip plan or calls tools."""
    print("---PLANNER: Planning Trip Step---")
    query = state['query']
    prefs = state.get('preferences', {})
    plan = state.get('current_plan', {})
    messages = state['messages']

    print(f"Current Query: {query}")
    print(f"Preferences: {prefs}")
    print(f"Current Plan: {plan}")

    # Placeholder: LLM call to decide next action (search flights, hotels, activities, or respond)
    # prompt = f"User query: {query}\nPreferences: {prefs}\nCurrent Plan: {plan}\nHistory:\n{messages}\nWhat is the next step or tool call?"
    # response = model_with_tools.invoke(prompt)

    # Simulate decision based on plan state
    if not plan.get('destination'):
        plan['destination'] = "Paris" # Simulate LLM choosing destination
        response = AIMessage(content=f"Okay, let's plan a trip to {plan['destination']}. How many days?")
    elif not plan.get('duration_days') and "days" in query.lower():
         try:
             days = int(query.split("days")[0].split()[-1]) # Very simple extraction
             plan['duration_days'] = days
             # Decide to search flights
             tool_call = ToolMessage(tool_call_id="flight_1", name="search_flights", content='{"departure": "NYC", "destination": "Paris", "date": "2025-10-10"}')
             response = AIMessage(content="", tool_calls=[tool_call])
         except:
              response = AIMessage(content="Sorry, I couldn't understand the number of days.")
    elif plan.get('duration_days') and not plan.get('flight_info'):
         # Assume flight search was the last step, now search hotels
         tool_call = ToolMessage(tool_call_id="hotel_1", name="search_hotels", content=f'{{"location": "{plan["destination"]}", "nights": {plan["duration_days"]}}}')
         response = AIMessage(content="", tool_calls=[tool_call])
    elif plan.get('flight_info') and plan.get('hotel_info') and not plan.get('activities'):
         plan['activities'] = ["Visit Eiffel Tower", "Louvre Museum"] # Simulate activity planning
         response = AIMessage(content=f"Okay, I've added flights, hotels, and activities: {plan}. Does this look good?")
    else:
         # Fallback response
         response = AIMessage(content="How else can I help you plan your trip?")


    return {"messages": [response], "current_plan": plan}

def execute_tools(state: PlannerState) -> dict:
    """Executes the tools called by the planner."""
    print("---PLANNER TOOL EXECUTOR: Running tools---")
    last_message = state['messages'][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {}

    tool_messages = []
    plan_updates = state['current_plan'].copy()

    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name'] # Access name from the dict-like tool_call
        tool_to_call = TOOL_MAP.get(tool_name)
        if not tool_to_call:
            result = f"Error: Tool '{tool_name}' not found."
        else:
            try:
                args = tool_call['args'] # Access args from the dict-like tool_call
                result = tool_to_call.invoke(args)
                # Update plan based on tool result
                if tool_name == "search_flights":
                    plan_updates['flight_info'] = str(result)
                elif tool_name == "search_hotels":
                    plan_updates['hotel_info'] = str(result)
            except Exception as e:
                result = f"Error executing tool '{tool_name}': {e}"

        tool_messages.append(ToolMessage(content=str(result), tool_call_id=tool_call['id']))

    return {"messages": tool_messages, "current_plan": plan_updates}

# --- Routing Functions ---
def route_after_planning(state: PlannerState) -> Literal["execute_tools", "__end__"]:
    """Decide whether to execute tools or end."""
    last_message = state['messages'][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "execute_tools"
    else:
        # End if the plan is complete or no tools called
        plan = state.get('current_plan', {})
        if plan.get('activities'): # Example end condition
             return END
        else: # Loop back to planning if more steps needed but no tool called
             # This path might indicate needing more user input or refinement
             # For simplicity, we end here, but could loop or ask user
             return END


# --- Graph Definition ---
planner_workflow = StateGraph(PlannerState)

planner_workflow.add_node("load_preferences", load_or_request_preferences)
planner_workflow.add_node("update_preferences", update_preferences_in_store)
planner_workflow.add_node("plan_step", plan_trip_step)
planner_workflow.add_node("execute_tools", execute_tools)

planner_workflow.add_edge(START, "load_preferences")
planner_workflow.add_edge("load_preferences", "update_preferences") # Always try to update based on latest query
planner_workflow.add_edge("update_preferences", "plan_step")
planner_workflow.add_conditional_edges(
    "plan_step",
    route_after_planning,
    {
        "execute_tools": "execute_tools",
        END: END
    }
)
planner_workflow.add_edge("execute_tools", "plan_step") # Loop back after executing tools

# --- Compile the Graph ---
# Requires checkpointer and store
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.store.memory import InMemoryStore

# checkpointer = MemorySaver()
# store = InMemoryStore() # Or use a persistent store like PostgresStore
# personalized_planner_agent = planner_workflow.compile(checkpointer=checkpointer, store=store)
personalized_planner_agent = planner_workflow.compile() # Needs checkpointer/store at runtime

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     from langgraph.store.memory import InMemoryStore
#     import uuid

#     checkpointer = MemorySaver()
#     store = InMemoryStore()

#     USER_ID = "user_123"
#     THREAD_ID = str(uuid.uuid4())
#     config = {"configurable": {"thread_id": THREAD_ID}}

#     print("--- Run 1: Initial query ---")
#     initial_state = {
#         "user_id": USER_ID,
#         "query": "Plan a 5 day trip for me.",
#         "messages": [HumanMessage(content="Plan a 5 day trip for me.")],
#         "current_plan": {}
#     }
#     for event in personalized_planner_agent.stream(initial_state, config=config):
#         print(event)

#     print("\n--- Run 2: Provide duration ---")
#     # State is loaded from checkpoint
#     for event in personalized_planner_agent.stream({"query": "5 days", "messages": [HumanMessage(content="5 days")]}, config=config):
#         print(event)

#     print("\n--- Run 3: (Implicitly uses checkpointed state) ---")
#     # Planner should now search hotels based on state
#     for event in personalized_planner_agent.stream(None, config=config):
#         print(event)

#     final_state = personalized_planner_agent.get_state(config)
#     print("\nFinal Plan:", final_state.values.get('current_plan'))
#     # Check preferences stored
#     # print("\nStored Preferences:", list(store.search(("preferences", USER_ID))))