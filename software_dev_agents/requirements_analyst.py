# software_dev_agents/requirements_analyst.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.types import interrupt, Command # Import interrupt

# --- State Definition ---
# This state might be a subset of the main ProjectState or managed separately.
# For this example, let's assume it receives the task to work on.

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str] # Agent name
    result: Optional[str]

class RequirementsState(TypedDict):
    """State specific to the requirements gathering process."""
    task_in_progress: Optional[Task] # The specific task assigned by the PM
    clarifying_question_needed: bool # Flag to decide if clarification is needed
    user_clarification: Optional[str] # Store response from user interrupt
    gathered_requirements: Optional[str] # Final output
    messages: Annotated[List[BaseMessage], add_messages] # For interaction history within this agent

# --- Node Functions ---

def check_clarification_needed(state: RequirementsState) -> dict:
    """
    Checks the task description to see if user clarification is needed.
    Sets a flag in the state.
    """
    print("---REQUIREMENTS ANALYST: Checking if clarification needed---")
    task = state.get('task_in_progress')
    if not task:
        print("Error: No task assigned.")
        return {"clarifying_question_needed": False} # Should not happen

    # Placeholder Logic: Check if description is vague
    if "vague" in task['description'].lower() or "details" in task['description'].lower():
        print("Clarification identified as needed.")
        return {"clarifying_question_needed": True}
    else:
        print("No clarification needed.")
        return {"clarifying_question_needed": False}

def ask_clarifying_question(state: RequirementsState) -> dict:
    """
    If clarification is needed, formulate a question and interrupt execution
    to get input from the user.
    """
    print("---REQUIREMENTS ANALYST: Asking Clarifying Question (if needed)---")
    if not state.get('clarifying_question_needed'):
        print("Skipping clarification question.")
        return {} # No changes needed if clarification is not required

    task = state.get('task_in_progress')
    question = f"Regarding the task '{task['description']}', could you please provide more specific details?"
    print(f"Interrupting to ask user: {question}")

    # Interrupt execution and wait for user input via Command(resume=...)
    # The value passed to interrupt() is surfaced to the calling process.
    user_response = interrupt(f"Question for user: {question}")

    # When resumed, user_response will contain the value from Command(resume=...)
    print(f"Received user response: {user_response}")
    return {
        "user_clarification": user_response,
        "messages": [HumanMessage(content=user_response)] # Log interaction
    }

def document_requirements(state: RequirementsState) -> dict:
    """
    Generates the requirements document based on the task and any clarifications.
    Updates the task status and result.
    """
    print("---REQUIREMENTS ANALYST: Documenting Requirements---")
    task = state.get('task_in_progress')
    if not task:
         print("Error: No task in progress to document.")
         return {"gathered_requirements": "Error: No task found."}

    clarification = state.get("user_clarification", "")
    if clarification:
        clarification_text = f"\n\nUser Clarification Provided:\n{clarification}"
    else:
        clarification_text = "\n\nNo specific user clarification was provided."

    # Placeholder: Generate requirements text (LLM call in real scenario)
    requirements_doc = (
        f"**Requirements Document**\n\n"
        f"**Task:** {task['description']}\n\n"
        f"**Details:**\n"
        f"- Requirement 1 based on task.\n"
        f"- Requirement 2 derived from details."
        f"{clarification_text}"
    )
    print(f"Generated Requirements:\n{requirements_doc}")

    # Prepare the updated task data to be returned
    # The main graph will be responsible for merging this back into the overall task list
    updated_task_result = task.copy()
    updated_task_result['status'] = 'completed'
    updated_task_result['result'] = requirements_doc

    # This agent returns the final document and the updated task object
    return {
        "gathered_requirements": requirements_doc,
        "task_in_progress": updated_task_result # Return the updated task
    }

# --- Routing Function ---
def decide_to_ask_or_document(state: RequirementsState) -> Literal["ask_clarifying_question", "document_requirements"]:
    """Decides whether to ask a question or proceed to documentation."""
    if state.get("clarifying_question_needed"):
        return "ask_clarifying_question"
    else:
        return "document_requirements"

# --- Graph Definition ---
requirements_workflow = StateGraph(RequirementsState)

requirements_workflow.add_node("check_clarification", check_clarification_needed)
requirements_workflow.add_node("ask_clarifying_question", ask_clarifying_question)
requirements_workflow.add_node("document_requirements", document_requirements)

requirements_workflow.add_edge(START, "check_clarification")
requirements_workflow.add_conditional_edges(
    "check_clarification",
    decide_to_ask_or_document,
    {
        "ask_clarifying_question": "ask_clarifying_question",
        "document_requirements": "document_requirements"
    }
)
requirements_workflow.add_edge("ask_clarifying_question", "document_requirements")
requirements_workflow.add_edge("document_requirements", END)

# --- Compile the Graph ---
requirements_analyst_agent = requirements_workflow.compile()

# Note: This compiled graph needs to be integrated into the main project graph.
# The main graph will handle invoking this subgraph, managing the interrupt,
# and updating the overall project state based on the 'task_in_progress' output.