# software_dev_agents/frontend_lead.py
from typing import TypedDict, Optional, Literal, List, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str] # Agent name
    result: Optional[str]
    parent_task_id: Optional[str] # Link sub-tasks to parent

class FrontendLeadState(TypedDict):
    """State specific to the Frontend Lead."""
    main_task: Optional[Task] # The task assigned by the Project Manager
    sub_tasks: List[Task] # Tasks broken down for developers
    # messages: Annotated[List[BaseMessage], add_messages] # Optional: for internal lead communication
    next_developer: Optional[str] # Which developer to route to next

# --- Node Functions ---

def plan_frontend_work(state: FrontendLeadState) -> dict:
    """
    Breaks down the main frontend task into sub-tasks for developers.
    """
    print("---FRONTEND LEAD: Planning Frontend Work---")
    main_task = state.get('main_task')
    existing_sub_tasks = state.get('sub_tasks', [])

    if not main_task:
        print("Error: No main task assigned to Frontend Lead.")
        return {}

    # Avoid re-planning if sub-tasks already exist
    if existing_sub_tasks and all(t['status'] != 'pending' for t in existing_sub_tasks):
         print("Checking status of existing sub-tasks...")
         # Logic to check if all sub-tasks are done, potentially update main_task status
         all_sub_completed = all(t['status'] == 'completed' for t in existing_sub_tasks)
         if all_sub_completed:
             print("All frontend sub-tasks completed.")
             # Update main task status (to be returned)
             main_task['status'] = 'completed'
             main_task['result'] = "Frontend implementation complete based on sub-tasks."
             return {"main_task": main_task, "next_developer": None} # Signal completion
         else:
             # Find next developer task if needed (e.g., if one finished, assign next)
             # Placeholder: For now, just check completion
             print("Some sub-tasks still in progress or blocked.")
             return {"next_developer": None} # Wait for updates

    elif not existing_sub_tasks:
        print(f"Breaking down main task: {main_task['description']}")
        # Placeholder Logic: Break down task (LLM call in real scenario)
        sub_tasks = [
            Task(id=f"{main_task['id']}_sub1", description=f"Implement UI Component for {main_task['description']}", status="pending", assigned_to="Frontend Developer 1", result=None, parent_task_id=main_task['id']),
            Task(id=f"{main_task['id']}_sub2", description=f"Implement Logic/API integration for {main_task['description']}", status="pending", assigned_to="Frontend Developer 2", result=None, parent_task_id=main_task['id']),
        ]
        print(f"Created sub-tasks: {sub_tasks}")
        # Assign the first developer
        next_dev = sub_tasks[0]['assigned_to']
        return {"sub_tasks": sub_tasks, "next_developer": next_dev}

    return {} # No changes if already planned and waiting

def route_to_developers(state: FrontendLeadState) -> Literal["Frontend Developer 1", "Frontend Developer 2", "__end__"]:
    """
    Routes to the next assigned developer or ends if all sub-tasks are done.
    """
    print("---FRONTEND LEAD: Routing to Developers---")
    next_dev = state.get("next_developer")

    if next_dev:
        print(f"Routing to {next_dev}")
        return next_dev

    # Check if all sub-tasks are completed
    sub_tasks = state.get('sub_tasks', [])
    all_sub_completed = all(task['status'] == 'completed' for task in sub_tasks)
    if all_sub_completed and sub_tasks:
         print("All sub-tasks done, ending Frontend Lead flow.")
         return END # Signal back to the main graph

    # Placeholder: Add logic here to find the next pending developer task if needed
    pending_dev_tasks = [t for t in sub_tasks if t['status'] == 'pending']
    if pending_dev_tasks:
        print(f"Routing to next pending developer: {pending_dev_tasks[0]['assigned_to']}")
        return pending_dev_tasks[0]['assigned_to']


    print("No developers assigned or all work done. Ending.")
    return END

# --- Graph Definition ---
frontend_lead_workflow = StateGraph(FrontendLeadState)

frontend_lead_workflow.add_node("plan_frontend_work", plan_frontend_work)

frontend_lead_workflow.add_edge(START, "plan_frontend_work")

# This supervisor routes to specific developer agents (which would be other subgraphs)
frontend_lead_workflow.add_conditional_edges(
    "plan_frontend_work",
    route_to_developers,
    {
        "Frontend Developer 1": "plan_frontend_work", # Example: Loop back after assignment (needs actual dev nodes)
        "Frontend Developer 2": "plan_frontend_work", # Example: Loop back after assignment
        END: END
    }
)

# --- Compile the Graph ---
frontend_lead_agent = frontend_lead_workflow.compile()

# Note: This compiled graph needs integration into the main project graph.
# The main graph will invoke this, passing the 'main_task'.
# It will also need nodes for "Frontend Developer 1" and "Frontend Developer 2".
# This lead agent needs to receive updates about sub_task completion to re-plan.
# The current routing loops back to planning for simplicity, but a real implementation
# would route to the actual developer nodes and have edges coming back from them.