# software_dev_agents/ui_ux_designer.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START

# --- State Definition ---
# Assuming it receives the task and relevant requirements/stories

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str] # Agent name
    result: Optional[str]

class DesignerState(TypedDict):
    """State specific to the UI/UX design process."""
    task_in_progress: Optional[Task] # The specific task assigned by the PM
    requirements_summary: str # Relevant requirements/stories for the design task
    design_artifact: Optional[str] # Output of this agent (e.g., description of wireframes)

# --- Node Functions ---

def create_design(state: DesignerState) -> dict:
    """
    Analyzes requirements/stories and creates UI/UX design artifacts (wireframes/mockups description).
    """
    print("---UI/UX DESIGNER: Creating Design Artifacts---")
    requirements = state.get('requirements_summary', 'N/A')
    task = state.get('task_in_progress')

    if not task:
        print("Error: No design task assigned.")
        return {"design_artifact": "Error: No task found."}

    print(f"Designing UI/UX based on requirements summary:\n{requirements}")

    # Placeholder Logic: Generate design description (LLM call in real scenario)
    # Example: Describe wireframes for key screens
    design_description = (
        f"**UI/UX Design Artifacts (Description)**\n\n"
        f"**Task:** {task['description']}\n\n"
        f"**Wireframes:**\n"
        f"- **Homepage:** Layout includes header, hero section, product grid, footer.\n"
        f"- **Product Detail Page:** Image gallery, description, price, add-to-cart button.\n"
        f"- **Shopping Cart:** Item list, quantity adjustment, subtotal, checkout button.\n"
        f"- **Checkout Flow:** Shipping address, payment info, order summary.\n\n"
        f"**Mockups:** Visual design follows a modern, clean aesthetic using the brand's color palette."
    )
    print(f"Generated Design Description:\n{design_description}")

    return {"design_artifact": design_description}

def finalize_design_document(state: DesignerState) -> dict:
    """
    Finalizes the design description and updates the task status.
    """
    print("---UI/UX DESIGNER: Finalizing Document---")
    task = state.get('task_in_progress')
    design_artifact = state.get('design_artifact')

    if not task or not design_artifact:
        print("Error: Missing task or design artifact for finalization.")
        return {"task_in_progress": task} # Return original task if error

    # Prepare the updated task data
    updated_task_result = task.copy()
    updated_task_result['status'] = 'completed'
    updated_task_result['result'] = design_artifact # Store the design description in the task result

    print(f"Design task {task['id']} completed.")
    # This agent returns the updated task object
    return {"task_in_progress": updated_task_result}


# --- Graph Definition ---
designer_workflow = StateGraph(DesignerState)

designer_workflow.add_node("create_design", create_design)
designer_workflow.add_node("finalize_document", finalize_design_document)

designer_workflow.add_edge(START, "create_design")
designer_workflow.add_edge("create_design", "finalize_document")
designer_workflow.add_edge("finalize_document", END)

# --- Compile the Graph ---
ui_ux_designer_agent = designer_workflow.compile()

# Note: This compiled graph needs to be integrated into the main project graph.
# The main graph will pass the relevant 'task_in_progress' and 'requirements_summary'
# to this subgraph and receive the updated 'task_in_progress'.