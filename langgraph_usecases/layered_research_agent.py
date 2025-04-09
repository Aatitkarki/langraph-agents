# langgraph_usecases/layered_research_agent.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
# from langchain_openai import ChatOpenAI # Example model
# from langchain_community.tools.tavily_search import TavilySearchResults # Example tool

# --- State Definition ---
class ResearchTask(TypedDict):
    """A sub-task for research."""
    id: str
    question: str # Sub-question to research
    status: Literal["pending", "in_progress", "completed"]
    result: Optional[str]
    assigned_to: Literal["WebSearcher", "Summarizer"]

class ResearchState(TypedDict):
    """Overall state for the layered research system."""
    main_question: str
    sub_tasks: List[ResearchTask]
    final_report: Optional[str]
    # messages: Annotated[List[BaseMessage], add_messages] # Optional history
    next_agent: Optional[Literal["WebSearcher", "Summarizer", "Supervisor"]]

# --- Placeholder Models/Tools ---
# supervisor_model = ChatOpenAI(model="gpt-4o")
# web_search_tool = TavilySearchResults(max_results=3)
# summarizer_model = ChatOpenAI(model="gpt-4o-mini")

# --- Node Functions ---

# Top-Level Supervisor Agent
def supervisor_agent(state: ResearchState) -> dict:
    """
    Breaks down the main question, assigns tasks to specialized agents,
    and synthesizes the final report.
    """
    print("---SUPERVISOR: Planning & Synthesizing---")
    main_question = state['main_question']
    sub_tasks = state.get('sub_tasks', [])

    # Initial planning
    if not sub_tasks:
        print(f"Breaking down main question: {main_question}")
        # Placeholder: LLM call to break down the question
        tasks_to_create = [
            {"question": f"Find background info on {main_question}", "assignee": "WebSearcher"},
            {"question": f"Find recent developments about {main_question}", "assignee": "WebSearcher"},
        ]
        new_sub_tasks = [
            ResearchTask(id=f"task_{i}", question=t["question"], status="pending", assigned_to=t["assignee"], result=None)
            for i, t in enumerate(tasks_to_create)
        ]
        print(f"Created sub-tasks: {new_sub_tasks}")
        next_agent = new_sub_tasks[0]['assigned_to'] # Assign first task
        return {"sub_tasks": new_sub_tasks, "next_agent": next_agent}

    # Check status of sub-tasks and synthesize or assign next
    else:
        completed_tasks = [t for t in sub_tasks if t['status'] == 'completed']
        pending_tasks = [t for t in sub_tasks if t['status'] == 'pending']

        if pending_tasks:
            next_task = pending_tasks[0]
            print(f"Assigning next pending task: {next_task['id']} to {next_task['assigned_to']}")
            next_agent = next_task['assigned_to']
            # Mark task as in_progress (state update handled by main graph logic ideally)
            # next_task['status'] = 'in_progress' # This should be done carefully
            return {"next_agent": next_agent} # Route to the assigned agent

        elif len(completed_tasks) == len(sub_tasks):
            # All tasks done, synthesize report
            print("All sub-tasks completed. Synthesizing final report.")
            # Placeholder: LLM call to synthesize results
            results = "\n\n".join([f"**{t['question']}**:\n{t['result']}" for t in completed_tasks])
            final_report = f"**Research Report for: {main_question}**\n\n{results}\n\n(Report synthesized by Supervisor)"
            print("Final report generated.")
            return {"final_report": final_report, "next_agent": None} # Signal completion

        else:
             print("Waiting for in-progress tasks to complete.")
             return {"next_agent": None} # Wait state

# Specialized Agent: Web Searcher (Placeholder Node)
# In a real system, this would be a subgraph or a more complex node with tool calls
def web_searcher_agent(state: ResearchState) -> dict:
    """
    Performs web searches for assigned sub-tasks.
    """
    print("---WEB SEARCHER: Performing Search---")
    sub_tasks = state['sub_tasks']
    # Find the task assigned to this agent (assuming one at a time for simplicity)
    task_to_do = next((t for t in sub_tasks if t['assigned_to'] == 'WebSearcher' and t['status'] == 'pending'), None) # Simplified: find first pending

    if not task_to_do:
        print("Web Searcher: No pending tasks found.")
        return {"next_agent": "Supervisor"} # Go back to supervisor if no task

    print(f"Performing web search for: {task_to_do['question']}")
    # Placeholder: Simulate web search
    # search_results = web_search_tool.invoke({"query": task_to_do['question']})
    # result_text = "\n".join([r['content'] for r in search_results])
    result_text = f"Simulated web search result for '{task_to_do['question']}'."
    print("Web search complete.")

    # Update the specific task's status and result
    updated_tasks = []
    for task in sub_tasks:
        if task['id'] == task_to_do['id']:
            updated_task = task.copy()
            updated_task['status'] = 'completed'
            updated_task['result'] = result_text
            updated_tasks.append(updated_task)
        else:
            updated_tasks.append(task)

    return {"sub_tasks": updated_tasks, "next_agent": "Supervisor"} # Return control to supervisor

# Specialized Agent: Summarizer (Placeholder Node)
# Similar structure to WebSearcher, would take text and summarize
def summarizer_agent(state: ResearchState) -> dict:
    """
    Summarizes text provided in assigned sub-tasks.
    """
    print("---SUMMARIZER: Summarizing Text---")
    sub_tasks = state['sub_tasks']
    task_to_do = next((t for t in sub_tasks if t['assigned_to'] == 'Summarizer' and t['status'] == 'pending'), None)

    if not task_to_do:
        print("Summarizer: No pending tasks found.")
        return {"next_agent": "Supervisor"}

    print(f"Summarizing text for task: {task_to_do['question']}") # Question might contain text or ref
    text_to_summarize = task_to_do.get('input_text', task_to_do['question']) # Example input key
    # Placeholder: Simulate summarization
    # summary = summarizer_model.invoke(f"Summarize this: {text_to_summarize}").content
    summary = f"This is a summary of the text related to '{task_to_do['question']}'."
    print("Summarization complete.")

    # Update task status and result
    updated_tasks = []
    for task in sub_tasks:
        if task['id'] == task_to_do['id']:
            updated_task = task.copy()
            updated_task['status'] = 'completed'
            updated_task['result'] = summary
            updated_tasks.append(updated_task)
        else:
            updated_tasks.append(task)

    return {"sub_tasks": updated_tasks, "next_agent": "Supervisor"}

# --- Routing Function ---
def route_research(state: ResearchState) -> Literal["WebSearcher", "Summarizer", "Supervisor", "__end__"]:
    """Routes control based on the 'next_agent' field set by the agents."""
    next_agent = state.get("next_agent")
    final_report = state.get("final_report")

    print(f"Routing decision: next_agent='{next_agent}', final_report_exists={bool(final_report)}")

    if final_report:
        print("Routing to END.")
        return END # End if report is generated
    elif next_agent == "WebSearcher":
        return "WebSearcher"
    elif next_agent == "Summarizer":
        return "Summarizer"
    else: # Default back to supervisor to check status or if next_agent is None/Supervisor
        return "Supervisor"

# --- Graph Definition ---
research_workflow = StateGraph(ResearchState)

# Add nodes
research_workflow.add_node("Supervisor", supervisor_agent)
research_workflow.add_node("WebSearcher", web_searcher_agent)
research_workflow.add_node("Summarizer", summarizer_agent)

# Add entry point
research_workflow.add_edge(START, "Supervisor")

# Add routing edges
research_workflow.add_conditional_edges(
    "Supervisor",
    route_research,
    {
        "WebSearcher": "WebSearcher",
        "Summarizer": "Summarizer",
        END: END
    }
)
# Specialized agents always return to the supervisor
research_workflow.add_edge("WebSearcher", "Supervisor")
research_workflow.add_edge("Summarizer", "Supervisor")

# --- Compile the Graph ---
layered_research_agent = research_workflow.compile()

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     memory = MemorySaver()
#     config = {"configurable": {"thread_id": "research-1"}}
#     initial_state = {
#         "main_question": "What are the pros and cons of using LangGraph?",
#     }
#     for event in layered_research_agent.stream(initial_state, config=config):
#         print(event)
#         print("---")
#     final_state = layered_research_agent.get_state(config)
#     print("\nFinal Report:\n", final_state.values.get('final_report'))