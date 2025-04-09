# software_dev_agents/devops_engineer.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import time # To simulate long-running processes

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class DevOpsState(TypedDict):
    """State specific to the DevOps Engineer."""
    task_in_progress: Optional[Task] # The specific task assigned (e.g., setup CI, deploy)
    architecture_details: Optional[str] # Info about tech stack, cloud provider
    code_artifacts_location: Optional[str] # Where to find the code to deploy/test
    deployment_status: Optional[str] # Output: Status of deployment or CI/CD setup
    monitoring_report: Optional[str] # Output: Monitoring setup details or status

# --- Node Functions ---

def process_devops_task(state: DevOpsState) -> dict:
    """
    Processes the assigned DevOps task (setup CI/CD, deploy, configure monitoring, etc.).
    """
    print("---DEVOPS ENGINEER: Processing Task---")
    task = state.get('task_in_progress')
    architecture = state.get('architecture_details', 'N/A')
    code_location = state.get('code_artifacts_location', 'N/A')

    if not task:
        print("Error: No task assigned to DevOps Engineer.")
        return {"deployment_status": "Error: No task found."}

    print(f"Processing DevOps task: {task['description']}")
    print(f"Architecture context: {architecture}")
    print(f"Code location: {code_location}")

    # Placeholder Logic: Simulate different DevOps actions based on task description
    output = {}
    if "ci/cd" in task['description'].lower():
        print("Simulating CI/CD pipeline setup...")
        time.sleep(2) # Simulate time taken
        ci_cd_status = f"CI/CD pipeline configured using GitHub Actions for repo at {code_location}. Builds and tests run on push to main."
        print("CI/CD Setup Complete (Simulated)")
        output["deployment_status"] = ci_cd_status # Use deployment_status for general results
    elif "deploy" in task['description'].lower():
        print(f"Simulating deployment to staging environment...")
        time.sleep(3) # Simulate time taken
        deployment_status = f"Deployment successful to staging environment. Application accessible at staging.example.com. Based on {architecture}."
        print("Deployment Complete (Simulated)")
        output["deployment_status"] = deployment_status
    elif "monitor" in task['description'].lower():
        print("Simulating monitoring setup...")
        time.sleep(1) # Simulate time taken
        monitoring_report = f"Monitoring configured using Datadog/Prometheus (based on {architecture}). Alerts set for high CPU usage and 5xx errors."
        print("Monitoring Setup Complete (Simulated)")
        output["monitoring_report"] = monitoring_report
    else:
        print("Warning: Unknown DevOps task type.")
        output["deployment_status"] = "Processed generic DevOps task."

    return output

def finalize_devops_work(state: DevOpsState) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---DEVOPS ENGINEER: Finalizing Work---")
    task = state.get('task_in_progress')
    deployment_status = state.get('deployment_status')
    monitoring_report = state.get('monitoring_report')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = ""
    if deployment_status:
        final_result += f"Deployment/CI Status: {deployment_status}\n"
    if monitoring_report:
        final_result += f"Monitoring Report: {monitoring_report}\n"

    updated_task = task.copy()
    # Simple success assumption for placeholder
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result.strip() if final_result else "DevOps task processed."

    print(f"DevOps task {task['id']} completed.")
    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
devops_workflow = StateGraph(DevOpsState)

devops_workflow.add_node("process_devops_task", process_devops_task)
devops_workflow.add_node("finalize_work", finalize_devops_work)

devops_workflow.add_edge(START, "process_devops_task")
devops_workflow.add_edge("process_devops_task", "finalize_work")
devops_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
devops_engineer_agent = devops_workflow.compile()

# Note: This agent receives 'task_in_progress' and context,
# returns the updated 'task_in_progress' with status/results.