# software_dev_agents/support_engineer.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate troubleshooting outcomes

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str # Here, description would be the user-reported issue
    status: Literal["pending", "in_progress", "resolved", "escalated", "failed"]
    assigned_to: Optional[str]
    result: Optional[str] # Resolution steps or escalation details
    parent_task_id: Optional[str] # Could link to original feature task if known

class SupportEngineerState(TypedDict):
    """State specific to the Support Engineer."""
    task_in_progress: Optional[Task] # The support ticket/task assigned
    knowledge_base: Optional[str] # Access to documentation, past issues
    troubleshooting_steps: Optional[str] # Steps taken during troubleshooting
    resolution_or_escalation: Optional[str] # Output: Resolution provided or escalation details
    outcome: Optional[str] # Internal outcome of troubleshooting

# --- Node Functions ---

def troubleshoot_issue(state: SupportEngineerState) -> dict:
    """
    Troubleshoots the user-reported issue based on description and knowledge base.
    """
    print("---SUPPORT ENGINEER: Troubleshooting Issue---")
    task = state.get('task_in_progress')
    kb = state.get('knowledge_base', 'N/A')

    if not task:
        print("Error: No support task assigned.")
        return {"troubleshooting_steps": "Error: No task found."}

    print(f"Troubleshooting issue: {task['description']}")
    print(f"Consulting Knowledge Base: {kb[:100]}...") # Print snippet

    # Placeholder Logic: Simulate troubleshooting (LLM call, log analysis, KB search)
    steps_taken = [
        "1. Searched knowledge base for similar issues.",
        "2. Checked application logs for errors around the time of the report.",
        "3. Attempted to reproduce the issue in the staging environment."
    ]
    outcome = random.choice(["resolved", "escalated", "failed"]) # Simulate outcome

    if outcome == "resolved":
        resolution = "Found known issue in KB. Provided user with workaround: [Placeholder workaround]."
        print("Issue resolved with known workaround.")
        steps_taken.append(f"4. Resolution: {resolution}")
    elif outcome == "escalated":
        resolution = "Unable to resolve. Issue seems to be a bug in [Component X]. Escalating to development team."
        print("Issue requires escalation.")
        steps_taken.append(f"4. Escalation: {resolution}")
    else: # Failed
        resolution = "Failed to reproduce or resolve the issue after initial troubleshooting."
        print("Troubleshooting failed.")
        steps_taken.append(f"4. Outcome: {resolution}")


    troubleshooting_log = "**Troubleshooting Steps:**\n" + "\n".join(steps_taken)
    return {"troubleshooting_steps": troubleshooting_log, "resolution_or_escalation": resolution, "outcome": outcome}

def finalize_support_ticket(state: SupportEngineerState) -> dict:
    """
    Marks the support task as resolved, escalated, or failed and bundles the results.
    """
    print("---SUPPORT ENGINEER: Finalizing Support Ticket---")
    task = state.get('task_in_progress')
    troubleshooting_steps = state.get('troubleshooting_steps')
    resolution_or_escalation = state.get('resolution_or_escalation')
    outcome = state.get('outcome') # Get outcome from troubleshooting

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Update task status based on outcome
    updated_task = task.copy()
    if outcome == "resolved":
        updated_task['status'] = 'resolved'
    elif outcome == "escalated":
        updated_task['status'] = 'escalated' # A specific status for escalation
    else: # Failed
        updated_task['status'] = 'failed' # Or maybe 'needs_more_info'

    updated_task['result'] = f"{troubleshooting_steps}\n\n**Final Outcome:**\n{resolution_or_escalation}"

    print(f"Support task {task['id']} finalized with status: {updated_task['status']}.")
    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
support_engineer_workflow = StateGraph(SupportEngineerState)

support_engineer_workflow.add_node("troubleshoot_issue", troubleshoot_issue)
support_engineer_workflow.add_node("finalize_ticket", finalize_support_ticket)

support_engineer_workflow.add_edge(START, "troubleshoot_issue")
support_engineer_workflow.add_edge("troubleshoot_issue", "finalize_ticket")
support_engineer_workflow.add_edge("finalize_ticket", END)

# --- Compile the Graph ---
support_engineer_agent = support_engineer_workflow.compile()

# Note: This agent receives 'task_in_progress' and 'knowledge_base',
# returns the updated 'task_in_progress' with resolution/escalation details and status.
# The 'escalated' status would need to trigger routing back to the Project Manager or relevant Lead in the main graph.