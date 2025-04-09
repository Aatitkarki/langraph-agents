# software_dev_agents/backend_lead.py
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

class BackendLeadState(TypedDict):
    """State specific to the Backend Lead."""
    main_task: Optional[Task] # The task assigned by the Project Manager
    sub_tasks: List[Task] # Tasks broken down for developers
    # messages: Annotated[List[BaseMessage], add_messages] # Optional: for internal lead communication
    next_developer: Optional[str] # Which backend developer to route to next

# --- Node Functions ---

def plan_backend_work(state: BackendLeadState) -> dict:
    """
    Breaks down the main backend task into sub-tasks for developers.
    """
    print("---BACKEND LEAD: Planning Backend Work---")
    main_task = state.get('main_task')
    existing_sub_tasks = state.get('sub_tasks', [])

    if not main_task:
        print("Error: No main task assigned to Backend Lead.")
        return {}

    # Avoid re-planning if sub-tasks already exist and are being processed or done
    if existing_sub_tasks and all(t['status'] != 'pending' for t in existing_sub_tasks):
         print("Checking status of existing backend sub-tasks...")
         all_sub_completed = all(t['status'] == 'completed' for t in existing_sub_tasks)
         if all_sub_completed:
             print("All backend sub-tasks completed.")
             main_task['status'] = 'completed'
             main_task['result'] = "Backend implementation complete based on sub-tasks."
             return {"main_task": main_task, "next_developer": None} # Signal completion
         else:
             print("Some backend sub-tasks still in progress or blocked.")
             return {"next_developer": None} # Wait for updates

    elif not existing_sub_tasks:
        print(f"Breaking down main backend task: {main_task['description']}")
        # Placeholder Logic: Break down task (LLM call in real scenario)
        # Example: Create API endpoint task and data processing task
        sub_tasks = [
            Task(id=f"{main_task['id']}_sub_be1", description=f"Implement API endpoint for {main_task['description']}", status="pending", assigned_to="Backend Developer 1", result=None, parent_task_id=main_task['id']),
            Task(id=f"{main_task['id']}_sub_be2", description=f"Implement data logic/DB interaction for {main_task['description']}", status="pending", assigned_to="Backend Developer 2", result=None, parent_task_id=main_task['id']),
            # Potentially assign tasks to DB Admin as well
        ]
        print(f"Created backend sub-tasks: {sub_tasks}")
        # Assign the first developer
        next_dev = sub_tasks[0]['assigned_to']
        return {"sub_tasks": sub_tasks, "next_developer": next_dev}

    return {} # No changes if already planned and waiting

def route_to_backend_developers(state: BackendLeadState) -> Literal["Backend Developer 1", "Backend Developer 2", "Database Admin", "__end__"]:
    """
    Routes to the next assigned backend developer/admin or ends if all sub-tasks are done.
    """
    print("---BACKEND LEAD: Routing to Backend Developers---")
    next_dev = state.get("next_developer")

    if next_dev:
        print(f"Routing to {next_dev}")
        # Need to clear next_developer after routing once, or manage assignment flow better
        # For now, just return it. The main graph needs logic to update sub_task status
        # and potentially re-invoke the lead planner.
        return next_dev

    # Check if all sub-tasks are completed
    sub_tasks = state.get('sub_tasks', [])
    all_sub_completed = all(task['status'] == 'completed' for task in sub_tasks)
    if all_sub_completed and sub_tasks:
         print("All backend sub-tasks done, ending Backend Lead flow.")
         return END # Signal back to the main graph

    # Placeholder: Find next pending task if next_dev wasn't set
    pending_dev_tasks = [t for t in sub_tasks if t['status'] == 'pending']
    if pending_dev_tasks:
        assignee = pending_dev_tasks[0]['assigned_to']
        print(f"Routing to next pending backend resource: {assignee}")
        return assignee # Could be Dev1, Dev2, or DB Admin

    print("No backend developers assigned or all work done. Ending.")
    return END

# --- Graph Definition ---
backend_lead_workflow = StateGraph(BackendLeadState)

backend_lead_workflow.add_node("plan_backend_work", plan_backend_work)

backend_lead_workflow.add_edge(START, "plan_backend_work")

# This supervisor routes to specific backend agents
backend_lead_workflow.add_conditional_edges(
    "plan_backend_work",
    route_to_backend_developers,
    {
        "Backend Developer 1": "plan_backend_work", # Example loop back
        "Backend Developer 2": "plan_backend_work", # Example loop back
        "Database Admin": "plan_backend_work",      # Example loop back
        END: END
    }
)

# --- Compile the Graph ---
backend_lead_agent = backend_lead_workflow.compile()

# Note: Needs integration into the main graph with actual developer/admin nodes.
# Requires updates on sub_task completion to function correctly.