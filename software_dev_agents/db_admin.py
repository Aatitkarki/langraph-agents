# software_dev_agents/db_admin.py
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

class DbAdminState(TypedDict):
    """State specific to the Database Admin."""
    task_in_progress: Optional[Task] # The specific sub-task assigned by the Backend Lead or PM
    architecture_details: Optional[str] # Relevant details from Architect
    requirements_summary: Optional[str] # Relevant requirements
    db_schema: Optional[str] # Output: SQL schema definition or migration script
    optimized_query: Optional[str] # Output: Optimized SQL query
    result_summary: Optional[str] # For generic tasks

# --- Node Functions ---

def process_db_task(state: DbAdminState) -> dict:
    """
    Processes the assigned database task (design schema, optimize query, etc.).
    """
    print("---DATABASE ADMIN: Processing DB Task---")
    task = state.get('task_in_progress')
    architecture = state.get('architecture_details', 'N/A')
    requirements = state.get('requirements_summary', 'N/A')

    if not task:
        print("Error: No task assigned to Database Admin.")
        return {"db_schema": "Error: No task found.", "optimized_query": None}

    print(f"Processing DB task: {task['description']}")
    print(f"Architecture context: {architecture}")
    print(f"Requirements context: {requirements}")

    # Placeholder Logic: Determine task type and generate output (LLM call)
    output = {}
    if "design schema" in task['description'].lower():
        # Generate Schema
        db_schema = f"""
-- SQL Schema for task: {task['description']}
-- Based on: {architecture} and {requirements}

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER DEFAULT 0
);

-- Add other tables like orders, cart_items etc. based on requirements
        """
        print("Generated DB Schema (Placeholder)")
        output["db_schema"] = db_schema
    elif "optimize query" in task['description'].lower():
        # Optimize Query
        optimized_query = f"""
-- Optimized Query for task: {task['description']}
-- Original query might be part of the description or state

SELECT p.name, p.price
FROM products p
JOIN categories c ON p.category_id = c.id -- Assuming category_id exists
WHERE c.name = 'Electronics' AND p.price > 100
ORDER BY p.price DESC
LIMIT 10;

-- Optimization applied: Added index on categories.name and products.price
        """
        print("Generated Optimized Query (Placeholder)")
        output["optimized_query"] = optimized_query
    else:
        print("Warning: Unknown DB task type.")
        output["result_summary"] = "Processed generic DB task." # Generic result

    return output

def finalize_db_work(state: DbAdminState) -> dict:
    """
    Marks the sub-task as completed and bundles the results.
    """
    print("---DATABASE ADMIN: Finalizing Work---")
    task = state.get('task_in_progress')
    db_schema = state.get('db_schema')
    optimized_query = state.get('optimized_query')
    result_summary = state.get('result_summary') # For generic tasks

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = ""
    if db_schema:
        final_result += f"DB Schema:\n```sql\n{db_schema}\n```\n"
    if optimized_query:
        final_result += f"Optimized Query:\n```sql\n{optimized_query}\n```\n"
    if result_summary and not (db_schema or optimized_query):
         final_result = result_summary

    updated_task = task.copy()
    updated_task['status'] = 'completed'
    updated_task['result'] = final_result.strip() if final_result else "DB task processed."

    print(f"Database Admin task {task['id']} completed.")
    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
db_admin_workflow = StateGraph(DbAdminState)

db_admin_workflow.add_node("process_db_task", process_db_task)
db_admin_workflow.add_node("finalize_work", finalize_db_work)

db_admin_workflow.add_edge(START, "process_db_task")
db_admin_workflow.add_edge("process_db_task", "finalize_work")
db_admin_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
db_admin_agent = db_admin_workflow.compile()

# Note: This agent receives 'task_in_progress' and context,
# returns the updated 'task_in_progress'.