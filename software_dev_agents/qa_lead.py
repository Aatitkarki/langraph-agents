# software_dev_agents/qa_lead.py
from typing import TypedDict, Optional, Literal, List, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"] # Added 'failed' status
    assigned_to: Optional[str] # Agent name
    result: Optional[str]
    parent_task_id: Optional[str] # Link sub-tasks to parent

class QALeadState(TypedDict):
    """State specific to the QA Lead."""
    main_task: Optional[Task] # The testing task assigned by the Project Manager
    requirements_summary: Optional[str] # Relevant requirements for testing context
    feature_details: Optional[str] # Details of the feature/code to be tested
    test_plan: Optional[str] # Generated test plan
    sub_tasks: List[Task] # Testing tasks broken down for testers
    # messages: Annotated[List[BaseMessage], add_messages] # Optional: for internal lead communication
    next_tester: Optional[str] # Which QA tester to route to next

# --- Node Functions ---

def create_test_plan(state: QALeadState) -> dict:
    """
    Creates a test plan based on the main testing task and feature details.
    """
    print("---QA LEAD: Creating Test Plan---")
    main_task = state.get('main_task')
    requirements = state.get('requirements_summary', 'N/A')
    feature = state.get('feature_details', 'N/A')

    if not main_task:
        print("Error: No main task assigned to QA Lead.")
        return {}

    print(f"Creating test plan for task: {main_task['description']}")
    print(f"Based on requirements: {requirements}")
    print(f"And feature details: {feature}")

    # Placeholder Logic: Generate test plan (LLM call in real scenario)
    test_plan = f"""
**Test Plan: {main_task['description']}**

**1. Scope:**
   - Test the feature described in: {feature}
   - Verify against requirements: {requirements}

**2. Test Types:**
   - Manual Testing (Assigned to QA Tester 1)
   - Automated Testing (Assigned to QA Tester 2)

**3. Manual Test Cases:**
   - Case 1: Verify core functionality A.
   - Case 2: Verify edge case B.
   - Case 3: Exploratory testing around feature C.

**4. Automated Test Cases:**
   - Test 1: Automate UI flow for feature A.
   - Test 2: Automate API validation for feature A.

**5. Reporting:** Bugs to be reported in tracking system. Final report upon completion.
"""
    print("Generated Test Plan (Placeholder)")
    return {"test_plan": test_plan}

def assign_testing_tasks(state: QALeadState) -> dict:
    """
    Assigns specific testing tasks based on the test plan.
    """
    print("---QA LEAD: Assigning Testing Tasks---")
    main_task = state.get('main_task')
    test_plan = state.get('test_plan')
    existing_sub_tasks = state.get('sub_tasks', [])

    if not main_task or not test_plan:
        print("Error: Missing main task or test plan for assignment.")
        return {}

    # Avoid re-assigning if already done
    if existing_sub_tasks:
        print("Sub-tasks already assigned.")
        # Logic to check status and potentially re-assign or find next
        all_sub_done = all(t['status'] in ['completed', 'failed'] for t in existing_sub_tasks)
        if all_sub_done:
            print("All QA sub-tasks finished.")
            # Aggregate results and update main task status
            results = "\n".join([f"- {t['id']}: {t['status']} - {t.get('result', 'N/A')}" for t in existing_sub_tasks])
            main_task['status'] = 'completed' # Or 'failed' if any sub-task failed significantly
            main_task['result'] = f"QA Testing Complete.\nSummary:\n{results}"
            return {"main_task": main_task, "next_tester": None}
        else:
            print("Some QA sub-tasks still in progress.")
            return {"next_tester": None} # Wait for updates

    # Placeholder: Assign tasks based on plan
    sub_tasks = [
        Task(id=f"{main_task['id']}_manual", description="Execute manual test cases from plan", status="pending", assigned_to="QA Tester 1", result=None, parent_task_id=main_task['id']),
        Task(id=f"{main_task['id']}_auto", description="Implement and run automated tests from plan", status="pending", assigned_to="QA Tester 2", result=None, parent_task_id=main_task['id']),
    ]
    print(f"Assigned testing sub-tasks: {sub_tasks}")
    next_tester = sub_tasks[0]['assigned_to'] # Assign first tester
    return {"sub_tasks": sub_tasks, "next_tester": next_tester}


def route_to_testers(state: QALeadState) -> Literal["QA Tester 1", "QA Tester 2", "__end__"]:
    """
    Routes to the next assigned QA tester or ends if all testing is done.
    """
    print("---QA LEAD: Routing to Testers---")
    next_tester = state.get("next_tester")

    if next_tester:
        print(f"Routing to {next_tester}")
        return next_tester

    # Check if all sub-tasks are completed/failed
    sub_tasks = state.get('sub_tasks', [])
    all_sub_done = all(task['status'] in ['completed', 'failed'] for task in sub_tasks)
    if all_sub_done and sub_tasks:
         print("All QA sub-tasks done, ending QA Lead flow.")
         return END # Signal back to the main graph

    # Placeholder: Find next pending task if next_tester wasn't set
    pending_qa_tasks = [t for t in sub_tasks if t['status'] == 'pending']
    if pending_qa_tasks:
        assignee = pending_qa_tasks[0]['assigned_to']
        print(f"Routing to next pending QA tester: {assignee}")
        return assignee

    print("No testers assigned or all testing done. Ending.")
    return END

# --- Graph Definition ---
qa_lead_workflow = StateGraph(QALeadState)

qa_lead_workflow.add_node("create_test_plan", create_test_plan)
qa_lead_workflow.add_node("assign_testing_tasks", assign_testing_tasks)

qa_lead_workflow.add_edge(START, "create_test_plan")
qa_lead_workflow.add_edge("create_test_plan", "assign_testing_tasks")

# This supervisor routes to specific tester agents
qa_lead_workflow.add_conditional_edges(
    "assign_testing_tasks",
    route_to_testers,
    {
        "QA Tester 1": "assign_testing_tasks", # Example loop back
        "QA Tester 2": "assign_testing_tasks", # Example loop back
        END: END
    }
)

# --- Compile the Graph ---
qa_lead_agent = qa_lead_workflow.compile()

# Note: Needs integration into the main graph with actual tester nodes.
# Requires updates on sub_task completion.