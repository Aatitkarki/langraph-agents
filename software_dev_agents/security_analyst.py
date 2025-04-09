# software_dev_agents/security_analyst.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate finding vulnerabilities

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class SecurityAnalystState(TypedDict):
    """State specific to the Security Analyst."""
    task_in_progress: Optional[Task] # The specific task assigned (e.g., review code snippet X)
    artifact_to_review: Optional[str] # The code, config, or description to be reviewed
    security_report: Optional[str] # Output: Report of findings
    vulnerabilities_found: Optional[List[str]] # Internal list of found issues

# --- Node Functions ---

def analyze_for_vulnerabilities(state: SecurityAnalystState) -> dict:
    """
    Analyzes the provided artifact (code, config) for security vulnerabilities.
    """
    print("---SECURITY ANALYST: Analyzing for Vulnerabilities---")
    task = state.get('task_in_progress')
    artifact = state.get('artifact_to_review', 'N/A')

    if not task:
        print("Error: No task assigned to Security Analyst.")
        return {"security_report": "Error: No task found."}

    print(f"Analyzing artifact for task: {task['description']}")
    print(f"Artifact details (first 100 chars): {artifact[:100]}...")

    # Placeholder Logic: Simulate vulnerability scanning (LLM call or static analysis tool)
    vulnerabilities_found = []
    if random.random() < 0.3: # Simulate finding issues 30% of the time
        vuln_type = random.choice(["SQL Injection risk", "Cross-Site Scripting (XSS)", "Insecure Dependency", "Hardcoded Secret"])
        vulnerabilities_found.append(f"Potential {vuln_type} found in artifact related to '{task['description']}'. Recommendation: [Placeholder fix].")

    if not vulnerabilities_found:
        report = f"**Security Analysis Report**\n\n**Task:** {task['description']}\n\n**Findings:**\nNo major vulnerabilities identified in the provided artifact."
        print("No major vulnerabilities found (Simulated).")
    else:
        report = f"**Security Analysis Report**\n\n**Task:** {task['description']}\n\n**Vulnerabilities Found:**\n" + "\n".join([f"- {vuln}" for vuln in vulnerabilities_found])
        print(f"Found {len(vulnerabilities_found)} potential vulnerabilities (Simulated).")

    return {"security_report": report, "vulnerabilities_found": vulnerabilities_found} # Pass findings for status update

def finalize_security_review(state: SecurityAnalystState) -> dict:
    """
    Marks the sub-task as completed (potentially failed/blocked if critical issues found)
    and bundles the report.
    """
    print("---SECURITY ANALYST: Finalizing Review---")
    task = state.get('task_in_progress')
    security_report = state.get('security_report')
    vulnerabilities = state.get('vulnerabilities_found', [])

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Update task status based on findings
    updated_task = task.copy()
    if vulnerabilities:
        # Simple logic: mark as 'blocked' if any vulnerability found, requiring remediation
        updated_task['status'] = 'blocked'
        print(f"Task {task['id']} blocked due to security findings.")
    else:
        updated_task['status'] = 'completed'
        print(f"Task {task['id']} completed with no major security issues.")

    updated_task['result'] = security_report if security_report else "Security review processed."

    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
security_analyst_workflow = StateGraph(SecurityAnalystState)

security_analyst_workflow.add_node("analyze_vulnerabilities", analyze_for_vulnerabilities)
security_analyst_workflow.add_node("finalize_review", finalize_security_review)

security_analyst_workflow.add_edge(START, "analyze_vulnerabilities")
security_analyst_workflow.add_edge("analyze_vulnerabilities", "finalize_review")
security_analyst_workflow.add_edge("finalize_review", END)

# --- Compile the Graph ---
security_analyst_agent = security_analyst_workflow.compile()

# Note: This agent receives 'task_in_progress' and 'artifact_to_review',
# returns the updated 'task_in_progress' with report/status.