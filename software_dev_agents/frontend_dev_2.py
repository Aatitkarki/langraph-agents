# software_dev_agents/frontend_dev_2.py
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

class FrontendDev2State(TypedDict):
    """State specific to Frontend Developer 2."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the Frontend Lead
    component_details: Optional[str] # Details about the component needing logic (e.g., from Dev 1 or design)
    api_endpoint: Optional[str] # Info about the backend API endpoint to integrate with
    logic_code: Optional[str] # Output: Implemented logic/state management code
    integration_tests: Optional[str] # Output: Integration tests

# --- Node Functions ---

def implement_logic(state: FrontendDev2State) -> dict:
    """
    Implements the UI logic, state management, and API integration.
    """
    print("---FRONTEND DEV 2: Implementing Logic & API Integration---")
    task = state.get('task_in_progress')
    component_details = state.get('component_details', 'N/A')
    api_endpoint = state.get('api_endpoint', 'N/A')

    if not task:
        print("Error: No task assigned to Frontend Developer 2.")
        return {"logic_code": "Error: No task found."}

    print(f"Implementing logic for task: {task['description']}")
    print(f"Component Details: {component_details}")
    print(f"API Endpoint: {api_endpoint}")

    # Placeholder Logic: Generate logic code (LLM call or code generation tool)
    logic_code = f"""
// Logic for {task['description'].replace('Implement Logic/API integration for ', '')}.js
import {{ useState, useEffect }} from 'react';

const useComponentLogic = (componentProps) => {{
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {{
    const fetchData = async () => {{
      if ('{api_endpoint}' === 'N/A') return; // Don't fetch if no endpoint
      setLoading(true);
      setError(null);
      try {{
        // const response = await fetch('{api_endpoint}'); // Replace with actual fetch
        // if (!response.ok) throw new Error('Network response was not ok');
        // const result = await response.json();
        const result = {{ message: 'Placeholder data from {api_endpoint}' }}; // Placeholder fetch
        setData(result);
      }} catch (err) {{
        setError(err.message);
      }} finally {{
        setLoading(false);
      }}
    }};

    fetchData();
    // Add dependencies if needed, e.g., [api_endpoint, componentProps.id]
  }}, []); // Fetch data on mount

  // Add state management logic (e.g., handling user interactions) here

  return {{ data, loading, error }};
}};

export default useComponentLogic;
"""
    print("Generated Logic/API Code (Placeholder)")
    return {"logic_code": logic_code}

def write_integration_tests(state: FrontendDev2State) -> dict:
    """
    Writes integration tests for the logic and API interaction.
    """
    print("---FRONTEND DEV 2: Writing Integration Tests---")
    task = state.get('task_in_progress')
    logic_code = state.get('logic_code')
    api_endpoint = state.get('api_endpoint', 'N/A')

    if not task or not logic_code:
        print("Error: Missing task or logic code for writing tests.")
        return {"integration_tests": "Error: Cannot write tests."}

    print(f"Writing integration tests for task: {task['description']}")

    # Placeholder Logic: Generate integration tests (LLM call or test generation tool)
    integration_tests = f"""
// Test: {task['description'].replace('Implement Logic/API integration for ', '')}.integration.test.js
// Requires setting up mock service workers (MSW) or similar for API mocking

// import {{ renderHook, waitFor }} from '@testing-library/react';
// import useComponentLogic from './useComponentLogic'; // Assuming logic is in a hook

describe('{task['description'].replace('Implement Logic/API integration for ', '')} Integration', () => {{
  test('fetches data correctly on mount', async () => {{
    // Mock the API call to '{api_endpoint}' here
    // Example using hypothetical renderHook and waitFor
    // const {{ result }} = renderHook(() => useComponentLogic({{}}));
    // await waitFor(() => expect(result.current.loading).toBe(false));
    // expect(result.current.error).toBeNull();
    // expect(result.current.data).toEqual(/* Expected mock data */);
    console.log('Integration test placeholder for API: {api_endpoint}');
    expect(true).toBe(true); // Placeholder assertion
  }});

  // Add more tests for error handling, state updates, etc.
}});
"""
    print("Generated Integration Tests (Placeholder)")
    return {"integration_tests": integration_tests}


def finalize_logic_work(state: FrontendDev2State) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---FRONTEND DEV 2: Finalizing Work---")
    task = state.get('task_in_progress')
    logic_code = state.get('logic_code')
    integration_tests = state.get('integration_tests')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = f"Logic/API Code:\n```javascript\n{logic_code}\n```\n\nIntegration Tests:\n```javascript\n{integration_tests}\n```"
    updated_task = task.copy()
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result

    print(f"Frontend Dev 2 task {task['id']} completed.")
    # Return the updated task object to be handled by the lead/main graph
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
frontend_dev_2_workflow = StateGraph(FrontendDev2State)

frontend_dev_2_workflow.add_node("implement_logic", implement_logic)
frontend_dev_2_workflow.add_node("write_integration_tests", write_integration_tests)
frontend_dev_2_workflow.add_node("finalize_work", finalize_logic_work)

frontend_dev_2_workflow.add_edge(START, "implement_logic")
frontend_dev_2_workflow.add_edge("implement_logic", "write_integration_tests")
frontend_dev_2_workflow.add_edge("write_integration_tests", "finalize_work")
frontend_dev_2_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
frontend_dev_2_agent = frontend_dev_2_workflow.compile()

# Note: This agent receives 'task_in_progress' and potentially 'component_details', 'api_endpoint'
# from the Frontend Lead and returns the updated 'task_in_progress'.