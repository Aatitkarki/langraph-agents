# software_dev_agents/backend_dev_1.py
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END, START

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class BackendDev1State(TypedDict):
    """State specific to Backend Developer 1."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the Backend Lead
    architecture_details: Optional[str] # Relevant details from Architect (e.g., framework choice)
    api_code: Optional[str] # Output: Implemented API endpoint code
    tests_code: Optional[str] # Output: Unit/integration tests for the endpoint

# --- Node Functions ---

def implement_api_endpoint(state: BackendDev1State) -> dict:
    """
    Implements the API endpoint based on the task description and architecture details.
    """
    print("---BACKEND DEV 1: Implementing API Endpoint---")
    task = state.get('task_in_progress')
    architecture = state.get('architecture_details', 'Defaulting to FastAPI') # Example default

    if not task:
        print("Error: No task assigned to Backend Developer 1.")
        return {"api_code": "Error: No task found."}

    print(f"Implementing API endpoint for task: {task['description']}")
    print(f"Based on architecture: {architecture}")

    # Placeholder Logic: Generate API code (LLM call or code generation tool)
    # Assuming FastAPI based on architecture details or default
    endpoint_name = task['description'].replace('Implement API endpoint for ', '').lower().replace(' ', '_')
    api_code = f"""
# Endpoint: /api/{endpoint_name}
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/api/{endpoint_name}", tags=["{endpoint_name}"])
async def {endpoint_name}_endpoint(payload: dict):
    '''
    API endpoint for {task['description']}.
    Requires payload validation (e.g., using Pydantic models).
    '''
    print(f"Received payload for {endpoint_name}: {{payload}}")
    # Business logic implementation goes here
    # Example: process data, interact with services/DB
    try:
        # result = process_data(payload) # Placeholder for business logic
        result = {{"status": "success", "message": "Data processed for {endpoint_name}"}}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include necessary imports and potentially Pydantic models for validation
"""
    print("Generated API Endpoint Code (Placeholder)")
    return {"api_code": api_code}

def write_backend_tests(state: BackendDev1State) -> dict:
    """
    Writes unit/integration tests for the implemented API endpoint and logic.
    """
    print("---BACKEND DEV 1: Writing Backend Tests---")
    task = state.get('task_in_progress')
    api_code = state.get('api_code')

    if not task or not api_code:
        print("Error: Missing task or API code for writing tests.")
        return {"tests_code": "Error: Cannot write tests."}

    print(f"Writing tests for API endpoint related to task: {task['description']}")

    # Placeholder Logic: Generate tests (LLM call or test generation tool)
    endpoint_name = task['description'].replace('Implement API endpoint for ', '').lower().replace(' ', '_')
    tests_code = f"""
# Test: test_{endpoint_name}.py
from fastapi.testclient import TestClient
# Assuming your FastAPI app instance is available for testing
# from main import app # Adjust import as needed

# client = TestClient(app)

def test_{endpoint_name}_success():
    '''Tests successful processing via the {endpoint_name} endpoint.'''
    payload = {{ "key": "value" }} # Example payload
    # response = client.post("/api/{endpoint_name}", json=payload)
    # assert response.status_code == 200
    # assert response.json()["status"] == "success"
    print(f"Placeholder success test for /api/{endpoint_name}")
    assert True

def test_{endpoint_name}_failure():
    '''Tests failure scenario for the {endpoint_name} endpoint.'''
    payload = {{ "invalid_key": "value" }} # Example invalid payload
    # response = client.post("/api/{endpoint_name}", json=payload)
    # assert response.status_code != 200 # Or specific error code like 422 or 500
    print(f"Placeholder failure test for /api/{endpoint_name}")
    assert True

# Add more tests for edge cases, validation, business logic, etc.
"""
    print("Generated Backend Tests (Placeholder)")
    return {"tests_code": tests_code}


def finalize_backend_work(state: BackendDev1State) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---BACKEND DEV 1: Finalizing Work---")
    task = state.get('task_in_progress')
    api_code = state.get('api_code')
    tests_code = state.get('tests_code')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = f"API Endpoint Code:\n```python\n{api_code}\n```\n\nTests Code:\n```python\n{tests_code}\n```"
    updated_task = task.copy()
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result

    print(f"Backend Dev 1 task {task['id']} completed.")
    # Return the updated task object to be handled by the lead/main graph
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
backend_dev_1_workflow = StateGraph(BackendDev1State)

backend_dev_1_workflow.add_node("implement_api_endpoint", implement_api_endpoint)
backend_dev_1_workflow.add_node("write_backend_tests", write_backend_tests)
backend_dev_1_workflow.add_node("finalize_work", finalize_backend_work)

backend_dev_1_workflow.add_edge(START, "implement_api_endpoint")
backend_dev_1_workflow.add_edge("implement_api_endpoint", "write_backend_tests")
backend_dev_1_workflow.add_edge("write_backend_tests", "finalize_work")
backend_dev_1_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
backend_dev_1_agent = backend_dev_1_workflow.compile()

# Note: This agent receives 'task_in_progress' and potentially 'architecture_details'
# from the Backend Lead and returns the updated 'task_in_progress'.