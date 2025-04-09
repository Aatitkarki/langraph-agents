# software_dev_agents/architect.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START

# --- State Definition ---
# Assuming it receives the task and requirements document

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str] # Agent name
    result: Optional[str]

class ArchitectState(TypedDict):
    """State specific to the architecture design process."""
    task_in_progress: Optional[Task] # The specific task assigned by the PM
    project_goal: str # Received from overall state
    requirements_document: str # Received from Requirements Analyst output
    architecture_design: Optional[str] # Output of this agent

# --- Node Functions ---

def design_architecture(state: ArchitectState) -> dict:
    """
    Analyzes requirements and project goal to design the high-level architecture.
    """
    print("---ARCHITECT: Designing Architecture---")
    goal = state.get('project_goal', 'N/A')
    requirements = state.get('requirements_document', 'N/A')
    task = state.get('task_in_progress')

    if not task:
        print("Error: No architecture task assigned.")
        return {"architecture_design": "Error: No task found."}

    print(f"Designing architecture for goal: {goal}")
    print(f"Based on requirements:\n{requirements}")

    # Placeholder Logic: Generate architecture design (LLM call in real scenario)
    # Example: Decide between Monolith/Microservices, choose tech stack
    design_choices = [
        "Architecture Style: Microservices",
        "Frontend Tech: React",
        "Backend Tech: Python (FastAPI)",
        "Database: PostgreSQL",
        "Cloud Provider: AWS",
        "Key Services: User Service, Product Service, Order Service, Payment Gateway Integration"
    ]
    architecture_doc = (
        f"**High-Level Architecture Design**\n\n"
        f"**Project Goal:** {goal}\n\n"
        f"**Key Decisions:**\n" + "\n".join([f"- {choice}" for choice in design_choices]) +
        f"\n\n**Rationale:** Based on scalability needs derived from requirements."
    )
    print(f"Generated Architecture Design:\n{architecture_doc}")

    return {"architecture_design": architecture_doc}

def finalize_architecture_document(state: ArchitectState) -> dict:
    """
    Finalizes the architecture document and updates the task status.
    """
    print("---ARCHITECT: Finalizing Document---")
    task = state.get('task_in_progress')
    architecture_design = state.get('architecture_design')

    if not task or not architecture_design:
        print("Error: Missing task or design for finalization.")
        # Handle error state appropriately, maybe return original task or error message
        return {"task_in_progress": task} # Return original task if error

    # Prepare the updated task data
    updated_task_result = task.copy()
    updated_task_result['status'] = 'completed'
    updated_task_result['result'] = architecture_design # Store the design in the task result

    print(f"Architecture task {task['id']} completed.")
    # This agent returns the updated task object
    # The main graph will merge this back into the overall ProjectState.tasks
    return {"task_in_progress": updated_task_result}


# --- Graph Definition ---
architect_workflow = StateGraph(ArchitectState)

architect_workflow.add_node("design_architecture", design_architecture)
architect_workflow.add_node("finalize_document", finalize_architecture_document)

architect_workflow.add_edge(START, "design_architecture")
architect_workflow.add_edge("design_architecture", "finalize_document")
architect_workflow.add_edge("finalize_document", END)

# --- Compile the Graph ---
architect_agent = architect_workflow.compile()

# Note: This compiled graph needs to be integrated into the main project graph.
# The main graph will pass the relevant 'task_in_progress', 'project_goal',
# and 'requirements_document' to this subgraph and receive the updated
# 'task_in_progress' (with status 'completed' and the design in 'result').