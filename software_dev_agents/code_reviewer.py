# software_dev_agents/code_reviewer.py
from typing import TypedDict, Optional, Literal, List
from langgraph.graph import StateGraph, END, START
import random # To simulate finding review comments

# --- State Definition ---

class Task(TypedDict):
    """Represents a task to be completed. (Copied for clarity, ideally import)"""
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked", "failed", "needs_review", "review_approved", "review_rejected"] # Added review statuses
    assigned_to: Optional[str]
    result: Optional[str]
    parent_task_id: Optional[str]

class CodeReviewerState(TypedDict):
    """State specific to the Code Reviewer."""
    task_in_progress: Optional[Task] # The specific review task assigned
    code_to_review: Optional[str] # The code snippet or link to code
    coding_standards: Optional[str] # Link or summary of coding standards
    review_comments: Optional[str] # Output: Comments from the review
    review_status: Optional[Literal["approved", "rejected"]] # Output: Overall status

# --- Node Functions ---

def review_code(state: CodeReviewerState) -> dict:
    """
    Reviews the provided code against standards and best practices.
    """
    print("---CODE REVIEWER: Reviewing Code---")
    task = state.get('task_in_progress')
    code = state.get('code_to_review', 'N/A')
    standards = state.get('coding_standards', 'General best practices')

    if not task:
        print("Error: No task assigned to Code Reviewer.")
        return {"review_comments": "Error: No task found.", "review_status": "rejected"}

    print(f"Reviewing code for task: {task['description']}")
    print(f"Applying standards: {standards}")
    print(f"Code snippet (first 150 chars): {code[:150]}...")

    # Placeholder Logic: Simulate code review (LLM call analyzing code)
    comments = []
    rejected = False
    if random.random() < 0.4: # Simulate finding issues 40% of the time
        comment_type = random.choice(["Style nitpick", "Potential bug", "Refactoring suggestion", "Missing test coverage"])
        comments.append(f"- {comment_type}: [Placeholder details regarding '{task['description']}'].")
        if "bug" in comment_type or "Refactoring" in comment_type:
            rejected = True # Reject if more serious issues found

    if not comments:
        review_comments = "Code review completed. Looks good!"
        review_status = "approved"
        print("Code review approved (Simulated).")
    else:
        review_comments = "**Code Review Comments:**\n" + "\n".join(comments)
        review_status = "rejected" if rejected else "approved" # Approve even with minor comments
        print(f"Code review {review_status} with comments (Simulated).")

    return {"review_comments": review_comments, "review_status": review_status}

def finalize_code_review(state: CodeReviewerState) -> dict:
    """
    Marks the review task as completed and bundles the review comments and status.
    """
    print("---CODE REVIEWER: Finalizing Review---")
    task = state.get('task_in_progress')
    review_comments = state.get('review_comments')
    review_status = state.get('review_status')

    if not task:
        print("Error: No task to finalize.")
        return {}

    # Update task status based on review outcome
    updated_task = task.copy()
    if review_status == "approved":
        updated_task['status'] = 'review_approved'
    elif review_status == "rejected":
        updated_task['status'] = 'review_rejected' # Or maybe 'blocked' depending on workflow
    else:
         updated_task['status'] = 'blocked' # Default if review failed

    updated_task['result'] = review_comments if review_comments else "Review processed."

    print(f"Code review task {task['id']} finalized with status: {updated_task['status']}.")
    # Return the updated task object
    return {"task_in_progress": updated_task}

# --- Graph Definition ---
code_reviewer_workflow = StateGraph(CodeReviewerState)

code_reviewer_workflow.add_node("review_code", review_code)
code_reviewer_workflow.add_node("finalize_review", finalize_code_review)

code_reviewer_workflow.add_edge(START, "review_code")
code_reviewer_workflow.add_edge("review_code", "finalize_review")
code_reviewer_workflow.add_edge("finalize_review", END)

# --- Compile the Graph ---
code_reviewer_agent = code_reviewer_workflow.compile()

# Note: This agent receives 'task_in_progress', 'code_to_review', 'coding_standards',
# returns the updated 'task_in_progress' with review comments and status.