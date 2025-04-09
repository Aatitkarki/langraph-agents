# software_dev_agents/performance_analyst.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate performance metrics

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed"]
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class PerformanceAnalystState(TypedDict):
    """State specific to the Performance Analyst."""
    task_in_progress: Optional[Task] # The specific analysis task assigned
    performance_data_source: Optional[str] # E.g., link to monitoring dashboard, logs location
    analysis_report: Optional[str] # Output: Report with findings and recommendations

# --- Node Functions ---

def analyze_performance_data(state: PerformanceAnalystState) -> dict:
    """
    Analyzes performance data from the specified source to identify bottlenecks.
    """
    print("---PERFORMANCE ANALYST: Analyzing Performance Data---")
    task = state.get('task_in_progress')
    data_source = state.get('performance_data_source', 'N/A')

    if not task:
        print("Error: No task assigned to Performance Analyst.")
        return {"analysis_report": "Error: No task found."}

    print(f"Analyzing performance for task: {task['description']}")
    print(f"Data Source: {data_source}")

    # Placeholder Logic: Simulate analyzing performance data (LLM call or data analysis)
    bottlenecks = []
    recommendations = []
    avg_response_time = random.uniform(50, 500) # Simulate ms
    error_rate = random.uniform(0, 0.05) # Simulate %

    report_summary = f"Analysis based on data from {data_source}:\n"
    report_summary += f"- Average Response Time: {avg_response_time:.2f} ms\n"
    report_summary += f"- Error Rate: {error_rate*100:.2f}%\n"

    if avg_response_time > 300: # Example threshold
        bottlenecks.append("High average response time detected.")
        recommendations.append("Investigate database query performance and API call latency.")
    if error_rate > 0.02: # Example threshold
        bottlenecks.append("Elevated error rate observed.")
        recommendations.append("Review application logs for frequent exceptions (e.g., 5xx errors).")

    if not bottlenecks:
        report = f"**Performance Analysis Report**\n\n{report_summary}\n**Findings:**\nPerformance metrics are within acceptable limits. No major bottlenecks identified."
        print("Performance analysis complete. No major issues found (Simulated).")
    else:
        report = f"**Performance Analysis Report**\n\n{report_summary}\n**Bottlenecks Identified:**\n" + "\n".join([f"- {b}" for b in bottlenecks])
        report += "\n\n**Recommendations:**\n" + "\n".join([f"- {r}" for r in recommendations])
        print(f"Performance analysis complete. Found {len(bottlenecks)} potential bottlenecks (Simulated).")

    return {"analysis_report": report}

def finalize_performance_analysis(state: PerformanceAnalystState) -> dict:
    """
    Marks the analysis task as completed and bundles the report.
    """
    print("---PERFORMANCE ANALYST: Finalizing Analysis---")
    task = state.get('task_in_progress')
    analysis_report = state.get('analysis_report')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Update task status
    updated_task = task.copy()
    if analysis_report and "Error:" not in analysis_report:
        updated_task['status'] = 'completed'
        updated_task['result'] = analysis_report
        print(f"Performance analysis task {task['id']} completed.")
    else:
        updated_task['status'] = 'failed' # Or blocked
        updated_task['result'] = analysis_report or "Failed to generate performance report."
        print(f"Performance analysis task {task['id']} failed.")

    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
performance_analyst_workflow = StateGraph(PerformanceAnalystState)

performance_analyst_workflow.add_node("analyze_performance", analyze_performance_data)
performance_analyst_workflow.add_node("finalize_analysis", finalize_performance_analysis)

performance_analyst_workflow.add_edge(START, "analyze_performance")
performance_analyst_workflow.add_edge("analyze_performance", "finalize_analysis")
performance_analyst_workflow.add_edge("finalize_analysis", END)

# --- Compile the Graph ---
performance_analyst_agent = performance_analyst_workflow.compile()

# Note: This agent receives 'task_in_progress', 'performance_data_source',
# returns the updated 'task_in_progress' with the analysis report.