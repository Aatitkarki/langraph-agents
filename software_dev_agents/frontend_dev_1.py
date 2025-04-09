# software_dev_agents/frontend_dev_1.py
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

class FrontendDev1State(TypedDict):
    """State specific to Frontend Developer 1."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the Frontend Lead
    design_details: Optional[str] # Details from UI/UX designer artifact (passed via task description or state)
    component_code: Optional[str] # Output: Implemented component code
    unit_tests: Optional[str] # Output: Unit tests for the component

# --- Node Functions ---

def implement_component(state: FrontendDev1State) -> dict:
    """
    Implements the UI component based on the task description and design details.
    """
    print("---FRONTEND DEV 1: Implementing UI Component---")
    task = state.get('task_in_progress')
    design = state.get('design_details', 'No specific design details provided.')

    if not task:
        print("Error: No task assigned to Frontend Developer 1.")
        return {"component_code": "Error: No task found."}

    print(f"Implementing component for task: {task['description']}")
    print(f"Based on design: {design}")

    # Placeholder Logic: Generate component code (LLM call or code generation tool in real scenario)
    component_code = f"""
// Component: {task['description'].replace('Implement UI Component for ', '')}.jsx
import React from 'react';

const {task['description'].replace('Implement UI Component for ', '').replace(' ', '')} = (props) => {{
  // Implementation based on design: {design}
  return (
    <div className='component-placeholder'>
      <h2>{task['description'].replace('Implement ', '')}</h2>
      <p>Props: {{JSON.stringify(props)}}</p>
      {{/* More detailed implementation here */}}
    </div>
  );
}};

export default {task['description'].replace('Implement UI Component for ', '').replace(' ', '')};
"""
    print("Generated Component Code (Placeholder)")
    return {"component_code": component_code}

def write_unit_tests(state: FrontendDev1State) -> dict:
    """
    Writes unit tests for the implemented component.
    """
    print("---FRONTEND DEV 1: Writing Unit Tests---")
    task = state.get('task_in_progress')
    component_code = state.get('component_code')

    if not task or not component_code:
        print("Error: Missing task or component code for writing tests.")
        return {"unit_tests": "Error: Cannot write tests."}

    print(f"Writing unit tests for component related to task: {task['description']}")

    # Placeholder Logic: Generate unit tests (LLM call or test generation tool)
    unit_tests = f"""
// Test: {task['description'].replace('Implement UI Component for ', '')}.test.jsx
import React from 'react';
import {{ render, screen }} from '@testing-library/react';
import {task['description'].replace('Implement UI Component for ', '').replace(' ', '')} from './{task['description'].replace('Implement UI Component for ', '')}';

describe('{task['description'].replace('Implement UI Component for ', '')}', () => {{
  test('renders correctly', () => {{
    render(<{task['description'].replace('Implement UI Component for ', '').replace(' ', '')} />);
    // Add specific assertions based on component implementation
    expect(screen.getByText('{task['description'].replace('Implement ', '')}')).toBeInTheDocument();
  }});

  // Add more tests for props, interactions, etc.
}});
"""
    print("Generated Unit Tests (Placeholder)")
    return {"unit_tests": unit_tests}


def finalize_component_work(state: FrontendDev1State) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---FRONTEND DEV 1: Finalizing Work---")
    task = state.get('task_in_progress')
    component_code = state.get('component_code')
    unit_tests = state.get('unit_tests')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = f"Component Code:\n```jsx\n{component_code}\n```\n\nUnit Tests:\n```jsx\n{unit_tests}\n```"
    updated_task = task.copy()
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result

    print(f"Frontend Dev 1 task {task['id']} completed.")
    # Return the updated task object to be handled by the lead/main graph
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
frontend_dev_1_workflow = StateGraph(FrontendDev1State)

frontend_dev_1_workflow.add_node("implement_component", implement_component)
frontend_dev_1_workflow.add_node("write_unit_tests", write_unit_tests)
frontend_dev_1_workflow.add_node("finalize_work", finalize_component_work)

frontend_dev_1_workflow.add_edge(START, "implement_component")
frontend_dev_1_workflow.add_edge("implement_component", "write_unit_tests")
frontend_dev_1_workflow.add_edge("write_unit_tests", "finalize_work")
frontend_dev_1_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
frontend_dev_1_agent = frontend_dev_1_workflow.compile()

# Note: This agent receives 'task_in_progress' and potentially 'design_details'
# from the Frontend Lead and returns the updated 'task_in_progress'.