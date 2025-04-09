# software_dev_agents/project_manager.py
from typing import TypedDict, Annotated, Literal, List, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
# Assuming necessary models and tools are imported elsewhere or defined here
# from langchain_anthropic import ChatAnthropic # Example

# --- State Definition ---
class Task(TypedDict):
    """Represents a task to be completed."""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str] # Agent name
    result: Optional[str]

class ProjectState(TypedDict):
    """Represents the overall state of the project managed by the Project Manager."""
    project_goal: str
    tasks: List[Task]
    # Using add_messages reducer for conversation history if needed
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: Optional[str] # For routing decisions

# --- Model Initialization (Placeholder) ---
# model = ChatAnthropic(model="claude-3-5-sonnet-20240620") # Replace with actual model
# model_router = model.with_structured_output(RouterOutputSchema) # Define schema for routing

# --- Node Functions ---

def plan_and_assign(state: ProjectState) -> dict:
    """
    Analyzes the project goal, breaks it down into initial tasks,
    and assigns them to the appropriate starting agents (e.g., Requirements Analyst, Architect).
    """
    print("---PROJECT MANAGER: Planning and Assigning Tasks---")
    goal = state['project_goal']
    current_tasks = state.get('tasks', [])

    # Placeholder logic: In a real scenario, an LLM call would analyze the goal
    # and existing tasks to generate new tasks and assignments.
    new_tasks = []
    if not current_tasks: # Initial planning
        print(f"Planning based on goal: {goal}")
        # Example initial tasks
        new_tasks = [
            Task(id="req_1", description="Gather detailed requirements", status="pending", assigned_to="Requirements Analyst", result=None),
            Task(id="arch_1", description="Define initial architecture", status="pending", assigned_to="Architect", result=None),
        ]
        print(f"Assigning initial tasks: {new_tasks}")
    else:
        # Logic to handle updates from other agents and assign next steps
        print("Reviewing completed tasks and planning next steps...")
        # ... (LLM call to decide next steps based on completed tasks) ...
        pass # Placeholder for subsequent planning

    updated_tasks = current_tasks + new_tasks
    # Decide next agent based on assigned tasks (simplified)
    next_agent = new_tasks[0]['assigned_to'] if new_tasks else None # Route to first assigned agent

    return {"tasks": updated_tasks, "next_agent": next_agent}

def route_tasks(state: ProjectState) -> Literal["Requirements Analyst", "Architect", "Frontend Lead", "Backend Lead", "QA Lead", "__end__"]:
    """
    Routes control to the agent assigned the next pending task or ends if all tasks are done.
    """
    print("---PROJECT MANAGER: Routing---")
    next_agent = state.get("next_agent")
    tasks = state.get('tasks', [])

    if next_agent:
        print(f"Routing to: {next_agent}")
        return next_agent # Directly use the agent name decided in plan_and_assign

    # Fallback or end condition check
    all_completed = all(task['status'] == 'completed' for task in tasks)
    if all_completed and tasks:
        print("All tasks completed. Ending.")
        return END
    elif tasks:
         # Find the next pending task if next_agent wasn't set explicitly
        pending_tasks = [t for t in tasks if t['status'] == 'pending']
        if pending_tasks:
             print(f"Routing to next pending task assignee: {pending_tasks[0]['assigned_to']}")
             return pending_tasks[0]['assigned_to']

    print("No pending tasks or explicit next agent. Ending.")
    return END # Default to end if no route determined

# --- Graph Definition ---
project_workflow = StateGraph(ProjectState)

# Add nodes
project_workflow.add_node("planner", plan_and_assign)

# Add entry point
project_workflow.add_edge(START, "planner")

# Add conditional routing edge
# This edge determines where to go after the planner node runs.
# It calls 'route_tasks' which returns the name of the next node (agent) or END.
project_workflow.add_conditional_edges(
    "planner",
    route_tasks,
    # The dictionary maps the output of route_tasks to the actual node names.
    # We need to list all possible agents the router might return.
    {
        "Requirements Analyst": "planner", # Example: Loop back to planner after assignment (needs actual agent nodes)
        "Architect": "planner",          # Example: Loop back to planner
        "Frontend Lead": "planner",      # Example: Loop back to planner
        "Backend Lead": "planner",       # Example: Loop back to planner
        "QA Lead": "planner",            # Example: Loop back to planner
        END: END
    }
)

# --- Compile the Graph ---
# Note: This is just the PM agent graph. It needs actual nodes for the other agents
# to hand off to. For now, routing just loops back to the planner.
project_manager_agent = project_workflow.compile()

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     memory = MemorySaver()
#     config = {"configurable": {"thread_id": "proj-123"}}
#     initial_state = {
#         "project_goal": "Build a new e-commerce website with user login and product catalog.",
#         "messages": [HumanMessage(content="Let's start the project.")],
#         "tasks": []
#     }
#     for event in project_manager_agent.stream(initial_state, config=config):
#         print(event)