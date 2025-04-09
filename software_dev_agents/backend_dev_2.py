# software_dev_agents/backend_dev_2.py
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

class BackendDev2State(TypedDict):
    """State specific to Backend Developer 2."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the Backend Lead
    db_schema_details: Optional[str] # Relevant DB schema info from DB Admin or Architect
    data_logic_code: Optional[str] # Output: Implemented data processing/DB interaction code
    tests_code: Optional[str] # Output: Unit/integration tests for the data logic

# --- Node Functions ---

def implement_data_logic(state: BackendDev2State) -> dict:
    """
    Implements data processing logic and database interactions based on the task.
    """
    print("---BACKEND DEV 2: Implementing Data Logic & DB Interaction---")
    task = state.get('task_in_progress')
    db_schema = state.get('db_schema_details', 'No specific DB schema provided.')

    if not task:
        print("Error: No task assigned to Backend Developer 2.")
        return {"data_logic_code": "Error: No task found."}

    print(f"Implementing data logic for task: {task['description']}")
    print(f"Using DB Schema details: {db_schema}")

    # Placeholder Logic: Generate data logic code (LLM call or code generation tool)
    # Example: Python code using an ORM like SQLAlchemy or direct DB queries
    data_logic_code = f"""
# Data logic for: {task['description']}
# Assuming use of a hypothetical ORM or DB connection 'db_session'
# Needs actual schema info ({db_schema}) to be useful

def process_{task['id'].replace('-', '_')}(data_input):
    '''Processes data according to task: {task['description']}'''
    print(f"Processing data: {{data_input}}")
    # Placeholder: Query database, transform data, etc.
    # Example query (replace with actual logic):
    # user = db_session.query(User).filter_by(id=data_input.get('user_id')).first()
    # if not user:
    #     raise ValueError("User not found")
    # processed_data = {{ "user_name": user.name, "status": "processed" }}

    processed_data = {{ "input": data_input, "status": "processed_placeholder" }}
    print(f"Data processed successfully.")
    return processed_data

# Add necessary imports, model definitions (if using ORM), etc.
"""
    print("Generated Data Logic Code (Placeholder)")
    return {"data_logic_code": data_logic_code}

def write_data_logic_tests(state: BackendDev2State) -> dict:
    """
    Writes unit/integration tests for the implemented data logic.
    """
    print("---BACKEND DEV 2: Writing Data Logic Tests---")
    task = state.get('task_in_progress')
    data_logic_code = state.get('data_logic_code')

    if not task or not data_logic_code:
        print("Error: Missing task or data logic code for writing tests.")
        return {"tests_code": "Error: Cannot write tests."}

    print(f"Writing tests for data logic related to task: {task['description']}")

    # Placeholder Logic: Generate tests (LLM call or test generation tool)
    tests_code = f"""
# Test: test_data_logic_{task['id'].replace('-', '_')}.py
import unittest
# from your_module import process_{task['id'].replace('-', '_')} # Adjust import

class TestDataLogic_{task['id'].replace('-', '_')}(unittest.TestCase):

    def test_successful_processing(self):
        '''Tests successful data processing.'''
        # Setup mock data and potentially mock DB interactions
        mock_input = {{'user_id': 123, 'data': 'sample'}}
        # expected_output = {{ "user_name": "Mock User", "status": "processed" }}
        expected_output = {{ "input": mock_input, "status": "processed_placeholder" }} # Placeholder

        # result = process_{task['id'].replace('-', '_')}(mock_input)
        # self.assertEqual(result, expected_output)
        print(f"Placeholder success test for process_{task['id'].replace('-', '_')}")
        self.assertTrue(True) # Placeholder assertion

    def test_error_scenario(self):
        '''Tests a potential error scenario (e.g., user not found).'''
        mock_input = {{'user_id': 999}} # Non-existent user
        # Setup mock DB to raise error or return None
        # with self.assertRaises(ValueError):
        #     process_{task['id'].replace('-', '_')}(mock_input)
        print(f"Placeholder error test for process_{task['id'].replace('-', '_')}")
        self.assertTrue(True) # Placeholder assertion

# Add more tests for different data inputs, edge cases, etc.

if __name__ == '__main__':
    unittest.main()
"""
    print("Generated Data Logic Tests (Placeholder)")
    return {"tests_code": tests_code}


def finalize_data_logic_work(state: BackendDev2State) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---BACKEND DEV 2: Finalizing Work---")
    task = state.get('task_in_progress')
    data_logic_code = state.get('data_logic_code')
    tests_code = state.get('tests_code')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = f"Data Logic Code:\n```python\n{data_logic_code}\n```\n\nTests Code:\n```python\n{tests_code}\n```"
    updated_task = task.copy()
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result

    print(f"Backend Dev 2 task {task['id']} completed.")
    # Return the updated task object to be handled by the lead/main graph
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
backend_dev_2_workflow = StateGraph(BackendDev2State)

backend_dev_2_workflow.add_node("implement_data_logic", implement_data_logic)
backend_dev_2_workflow.add_node("write_data_logic_tests", write_data_logic_tests)
backend_dev_2_workflow.add_node("finalize_work", finalize_data_logic_work)

backend_dev_2_workflow.add_edge(START, "implement_data_logic")
backend_dev_2_workflow.add_edge("implement_data_logic", "write_data_logic_tests")
backend_dev_2_workflow.add_edge("write_data_logic_tests", "finalize_work")
backend_dev_2_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
backend_dev_2_agent = backend_dev_2_workflow.compile()

# Note: This agent receives 'task_in_progress' and potentially 'db_schema_details'
# from the Backend Lead and returns the updated 'task_in_progress'.