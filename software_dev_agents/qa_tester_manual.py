# software_dev_agents/qa_tester_manual.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate finding bugs

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class QATesterManualState(TypedDict):
    """State specific to the Manual QA Tester."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the QA Lead
    test_plan_details: Optional[str] # Relevant section of the test plan
    feature_details: Optional[str] # Details of the feature being tested
    test_report: Optional[str] # Output: Report of manual test execution and bugs found
    bugs_found: Optional[List[str]] # Store bugs found separately for status update logic

# --- Node Functions ---

def execute_manual_tests(state: QATesterManualState) -> dict:
    """
    Simulates executing manual test cases and exploratory testing.
    Generates a test report, potentially including simulated bug findings.
    """
    print("---QA TESTER 1 (Manual): Executing Manual Tests---")
    task = state.get('task_in_progress')
    test_plan = state.get('test_plan_details', 'N/A')
    feature = state.get('feature_details', 'N/A')

    if not task:
        print("Error: No task assigned to Manual QA Tester.")
        return {"test_report": "Error: No task found."}

    print(f"Executing manual tests for task: {task['description']}")
    print(f"Based on Test Plan section: {test_plan}")
    print(f"Testing Feature: {feature}")

    # Placeholder Logic: Simulate test execution and bug finding
    bugs_found = []
    test_summary = []

    # Simulate running test cases from the plan
    test_cases_executed = ["Case 1", "Case 2", "Case 3"] # Assume these were in the plan
    for case in test_cases_executed:
        # Simulate pass/fail/bug
        outcome = random.choice(["Passed", "Passed", "Passed", "Failed", "Bug Found"])
        test_summary.append(f"- {case}: {outcome}")
        if outcome == "Bug Found":
            bugs_found.append(f"BUG-{random.randint(100, 999)}: Issue found during {case} on feature '{feature}'. Details: [Placeholder details].")
        elif outcome == "Failed":
             bugs_found.append(f"FAILURE-{random.randint(100, 999)}: Test case {case} failed. Details: [Placeholder details].")


    # Simulate exploratory testing
    exploratory_summary = "Performed exploratory testing around usability and responsiveness. Found minor layout issue on mobile."
    bugs_found.append(f"BUG-{random.randint(100, 999)}: Minor layout issue on mobile during exploratory testing.")

    # Generate Report
    report = f"**Manual Test Execution Report**\n\n"
    report += f"**Task:** {task['description']}\n\n"
    report += "**Test Case Summary:**\n" + "\n".join(test_summary) + "\n\n"
    report += f"**Exploratory Testing Summary:**\n{exploratory_summary}\n\n"
    if bugs_found:
        report += "**Bugs/Failures Found:**\n" + "\n".join([f"- {bug}" for bug in bugs_found])
    else:
        report += "**Bugs/Failures Found:**\nNone"

    print("Generated Manual Test Report (Placeholder)")
    return {"test_report": report, "bugs_found": bugs_found} # Pass bugs separately if needed for status update

def finalize_manual_test_work(state: QATesterManualState) -> dict:
    """
    Marks the sub-task as completed (or failed) and bundles the results.
    """
    print("---QA TESTER 1 (Manual): Finalizing Work---")
    task = state.get('task_in_progress')
    test_report = state.get('test_report')
    bugs_found = state.get('bugs_found', []) # Get bugs found during execution

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Update task status based on findings
    updated_task = task.copy()
    if bugs_found:
        # Decide if any bug constitutes a failure or just completion with issues
        # Simple logic: if "FAILURE" in any bug report, mark as failed.
        if any("FAILURE" in bug for bug in bugs_found):
             updated_task['status'] = 'failed'
        else:
             updated_task['status'] = 'completed' # Completed, but with bugs noted
    else:
        updated_task['status'] = 'completed'

    updated_task['result'] = test_report if test_report else "Manual testing processed."

    print(f"Manual QA task {task['id']} finalized with status: {updated_task['status']}.")
    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
qa_tester_manual_workflow = StateGraph(QATesterManualState)

qa_tester_manual_workflow.add_node("execute_manual_tests", execute_manual_tests)
qa_tester_manual_workflow.add_node("finalize_work", finalize_manual_test_work)

qa_tester_manual_workflow.add_edge(START, "execute_manual_tests")
qa_tester_manual_workflow.add_edge("execute_manual_tests", "finalize_work")
qa_tester_manual_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
qa_tester_manual_agent = qa_tester_manual_workflow.compile()

# Note: This agent receives 'task_in_progress' and context,
# returns the updated 'task_in_progress' with test results/status.