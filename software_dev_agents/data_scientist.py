# software_dev_agents/data_scientist.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate analysis results

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class DataScientistState(TypedDict):
    """State specific to the Data Scientist."""
    task_in_progress: Optional[Task] # The specific analysis or modeling task assigned
    data_source: Optional[str] # Location of data to analyze (e.g., DB table, file path)
    analysis_requirements: Optional[str] # Specific questions or goals for the analysis/model
    analysis_report: Optional[str] # Output: Report of data analysis findings
    model_artifact: Optional[str] # Output: Path or description of the trained ML model

# --- Node Functions ---

def perform_data_analysis_or_modeling(state: DataScientistState) -> dict:
    """
    Performs data analysis or ML modeling based on the task description.
    """
    print("---DATA SCIENTIST: Performing Analysis/Modeling---")
    task = state.get('task_in_progress')
    data_source = state.get('data_source', 'N/A')
    requirements = state.get('analysis_requirements', 'N/A')

    if not task:
        print("Error: No task assigned to Data Scientist.")
        return {"analysis_report": "Error: No task found."}

    print(f"Processing Data Science task: {task['description']}")
    print(f"Data Source: {data_source}")
    print(f"Analysis Requirements: {requirements}")

    # Placeholder Logic: Simulate analysis or model training
    output = {}
    if "analyze" in task['description'].lower():
        print("Simulating data analysis...")
        # Simulate finding insights
        insight = random.choice([
            "User engagement peaks on weekends.",
            "Product category X has the highest conversion rate.",
            "There is a strong correlation between feature Y usage and retention."
        ])
        analysis_report = f"""
**Data Analysis Report**

**Task:** {task['description']}
**Data Source:** {data_source}

**Key Insight:**
- {insight}

**Methodology:** (Placeholder: Describe analysis methods)
- Aggregated user activity data.
- Calculated conversion rates per category.
- Performed correlation analysis.

**Next Steps:** Recommend A/B testing based on insight.
"""
        print(f"Analysis complete. Key insight: {insight}")
        output["analysis_report"] = analysis_report
    elif "model" in task['description'].lower():
        print("Simulating ML model training...")
        # Simulate training a model
        model_type = random.choice(["Recommendation Engine", "Churn Prediction", "Sentiment Analysis"])
        accuracy = random.uniform(0.75, 0.95)
        model_artifact_description = f"""
**ML Model Artifact (Description)**

**Task:** {task['description']}
**Model Type:** {model_type}
**Training Data:** {data_source}
**Performance:** Accuracy/AUC: {accuracy:.2f} (on validation set)
**Deployment:** Model saved to 'models/{task['id']}.pkl'. API endpoint needs to be created.
"""
        print(f"Model training complete. Type: {model_type}, Accuracy: {accuracy:.2f}")
        output["model_artifact"] = model_artifact_description
    else:
        print("Warning: Unknown Data Science task type.")
        output["analysis_report"] = "Processed generic data science task."

    return output

def finalize_ds_work(state: DataScientistState) -> dict:
    """
    Marks the data science task as completed and bundles the results.
    """
    print("---DATA SCIENTIST: Finalizing Work---")
    task = state.get('task_in_progress')
    analysis_report = state.get('analysis_report')
    model_artifact = state.get('model_artifact')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Combine results and update task status
    final_result = ""
    if analysis_report:
        final_result += f"Analysis Report:\n{analysis_report}\n"
    if model_artifact:
        final_result += f"Model Artifact:\n{model_artifact}\n"

    updated_task = task.copy()
    if final_result and "Error:" not in final_result:
        updated_task['status'] = 'completed'
        updated_task['result'] = final_result.strip()
        print(f"Data Science task {task['id']} completed.")
    else:
        updated_task['status'] = 'failed' # Or blocked
        updated_task['result'] = final_result or "Failed to process data science task."
        print(f"Data Science task {task['id']} failed.")

    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
data_scientist_workflow = StateGraph(DataScientistState)

data_scientist_workflow.add_node("perform_analysis_modeling", perform_data_analysis_or_modeling)
data_scientist_workflow.add_node("finalize_work", finalize_ds_work)

data_scientist_workflow.add_edge(START, "perform_analysis_modeling")
data_scientist_workflow.add_edge("perform_analysis_modeling", "finalize_work")
data_scientist_workflow.add_edge("finalize_work", END)

# --- Compile the Graph ---
data_scientist_agent = data_scientist_workflow.compile()

# Note: This agent receives 'task_in_progress', 'data_source', 'analysis_requirements',
# returns the updated 'task_in_progress' with the report or model details.