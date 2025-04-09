# langgraph_usecases/interactive_tutorial.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.types import interrupt, Command # Import interrupt and Command
# from langchain_openai import ChatOpenAI # Example model

# --- Tutorial Content (Example) ---
TUTORIAL_STEPS = [
    {"id": 1, "content": "Welcome! Step 1: What is LangGraph? It's a library for building stateful multi-actor applications.", "question": "What is LangGraph primarily used for? (a) Web development, (b) Building stateful applications, (c) Data analysis", "correct_answer_keyword": "stateful"},
    {"id": 2, "content": "Step 2: Key concepts are State, Nodes, and Edges.", "question": "Which of these is NOT a core LangGraph concept? (a) State, (b) Nodes, (c) Widgets", "correct_answer_keyword": "widgets"},
    {"id": 3, "content": "Step 3: You compile a graph to make it runnable.", "question": "What method is called to make a graph runnable? (a) .run(), (b) .compile(), (c) .execute()", "correct_answer_keyword": "compile"},
    {"id": 4, "content": "Congratulations! You've completed the tutorial.", "question": None, "correct_answer_keyword": None}, # Final step
]

# --- State Definition ---
class TutorialState(TypedDict):
    """Represents the state of the interactive tutorial."""
    current_step_id: int
    user_response: Optional[str]
    evaluation_result: Optional[Literal["correct", "incorrect"]]
    messages: Annotated[List[BaseMessage], add_messages] # History of interaction

# --- Placeholder Models ---
# evaluation_model = ChatOpenAI(model="gpt-4o-mini") # Could be used for more complex evaluation

# --- Node Functions ---

def present_step(state: TutorialState) -> dict:
    """Presents the content for the current tutorial step."""
    print("---TUTORIAL AGENT: Presenting Step---")
    step_id = state.get('current_step_id', 1) # Start at step 1 if not set
    current_step_data = next((step for step in TUTORIAL_STEPS if step["id"] == step_id), None)

    if not current_step_data:
        print(f"Error: Step ID {step_id} not found.")
        # End the tutorial if step not found
        return {"messages": [AIMessage(content="Error: Tutorial step not found.")], "current_step_id": step_id + 100} # Force end

    content = current_step_data["content"]
    print(f"Presenting Step {step_id}: {content}")

    # Add content to messages and reset evaluation for the new step
    return {"messages": [AIMessage(content=content)], "evaluation_result": None, "user_response": None}

def ask_question(state: TutorialState) -> dict:
    """Asks the question related to the current step, if any."""
    print("---TUTORIAL AGENT: Asking Question---")
    step_id = state['current_step_id']
    current_step_data = next((step for step in TUTORIAL_STEPS if step["id"] == step_id), None)
    question = current_step_data.get("question") if current_step_data else None

    if question:
        print(f"Asking: {question}")
        # Interrupt to get user's answer
        user_answer = interrupt(question) # The question itself is surfaced
        print(f"Received user answer: {user_answer}")
        return {"user_response": user_answer, "messages": [HumanMessage(content=user_answer)]}
    else:
        # If no question for this step (e.g., the last step)
        print("No question for this step.")
        return {"user_response": None} # Ensure user_response is cleared

def evaluate_response(state: TutorialState) -> dict:
    """Evaluates the user's response to the question."""
    print("---TUTORIAL AGENT: Evaluating Response---")
    step_id = state['current_step_id']
    user_response = state.get('user_response')
    current_step_data = next((step for step in TUTORIAL_STEPS if step["id"] == step_id), None)
    correct_keyword = current_step_data.get("correct_answer_keyword") if current_step_data else None

    if not user_response or not correct_keyword:
        print("No response to evaluate or no correct answer defined.")
        # If there was no question, consider it 'correct' to proceed
        return {"evaluation_result": "correct"}

    # Simple keyword check (replace with LLM evaluation for complex questions)
    if correct_keyword.lower() in user_response.lower():
        print("Evaluation: Correct")
        return {"evaluation_result": "correct"}
    else:
        print("Evaluation: Incorrect")
        return {"evaluation_result": "incorrect"}

def provide_feedback_and_next_step(state: TutorialState) -> dict:
    """Provides feedback and determines the next step ID."""
    print("---TUTORIAL AGENT: Providing Feedback & Next Step---")
    evaluation = state.get('evaluation_result')
    current_step_id = state['current_step_id']
    next_step_id = current_step_id # Default to repeating step if incorrect

    if evaluation == "correct":
        feedback_msg = "Correct! Moving to the next step."
        next_step_id = current_step_id + 1
        print(feedback_msg)
    elif evaluation == "incorrect":
        feedback_msg = "That wasn't quite right. Let's review this step again."
        # Keep current_step_id to repeat
        print(feedback_msg)
    else: # No evaluation happened (e.g., last step)
        feedback_msg = "" # No feedback needed
        next_step_id = current_step_id + 1 # Assume progression if no question/eval

    # Check if tutorial is finished
    if next_step_id > len(TUTORIAL_STEPS):
         print("Tutorial finished.")
         # No feedback needed, just update step ID to signal end
         return {"current_step_id": next_step_id}


    return {"messages": [AIMessage(content=feedback_msg)] if feedback_msg else [], "current_step_id": next_step_id}


# --- Routing Functions ---
def route_after_presentation(state: TutorialState) -> Literal["ask_question", "provide_feedback"]:
    """Routes after presenting step content."""
    step_id = state['current_step_id']
    current_step_data = next((step for step in TUTORIAL_STEPS if step["id"] == step_id), None)
    if current_step_data and current_step_data.get("question"):
        return "ask_question"
    else: # No question, go straight to feedback/next step logic
        return "provide_feedback"

def route_after_evaluation(state: TutorialState) -> Literal["provide_feedback"]:
     """Always provide feedback after evaluation."""
     return "provide_feedback"

def route_after_feedback(state: TutorialState) -> Literal["present_step", "__end__"]:
    """Routes to the next step or ends the tutorial."""
    next_step_id = state['current_step_id']
    if next_step_id > len(TUTORIAL_STEPS):
        return END
    else:
        return "present_step" # Go to the next (or repeated) step

# --- Graph Definition ---
tutorial_workflow = StateGraph(TutorialState)

tutorial_workflow.add_node("present_step", present_step)
tutorial_workflow.add_node("ask_question", ask_question)
tutorial_workflow.add_node("evaluate_response", evaluate_response)
tutorial_workflow.add_node("provide_feedback", provide_feedback_and_next_step)

tutorial_workflow.add_edge(START, "present_step") # Start with the first step presentation

tutorial_workflow.add_conditional_edges(
    "present_step",
    route_after_presentation,
    {"ask_question": "ask_question", "provide_feedback": "provide_feedback"}
)

tutorial_workflow.add_edge("ask_question", "evaluate_response")
tutorial_workflow.add_edge("evaluate_response", "provide_feedback")

tutorial_workflow.add_conditional_edges(
    "provide_feedback",
    route_after_feedback,
    {"present_step": "present_step", END: END}
)

# --- Compile the Graph ---
# Requires a checkpointer for interrupt to work
# from langgraph.checkpoint.memory import MemorySaver
# checkpointer = MemorySaver()
# interactive_tutorial_agent = tutorial_workflow.compile(checkpointer=checkpointer)
interactive_tutorial_agent = tutorial_workflow.compile() # Needs checkpointer at runtime

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     import uuid
#     memory = MemorySaver()
#     thread_id = str(uuid.uuid4())
#     config = {"configurable": {"thread_id": thread_id}}
#     current_state = {"current_step_id": 1} # Start at step 1

#     while True:
#         print("\nStarting/Resuming tutorial flow...")
#         events = interactive_tutorial_agent.stream(current_state, config=config)
#         interrupt_payload = None
#         for event in events:
#             # Print all events for debugging
#             print(event)
#             print("---")
#             # Check for interrupt
#             if "__interrupt__" in event:
#                 interrupt_payload = event["__interrupt__"][0].value
#                 break # Stop processing events after interrupt

#         if interrupt_payload:
#             print(f"\n>>> Question for User: {interrupt_payload}")
#             user_input = input("Your answer: ")
#             current_state = Command(resume=user_input) # Prepare resume command
#         else:
#             print("\nTutorial finished or ended unexpectedly.")
#             break # Exit loop if no interrupt (graph finished)

#         # Clear current_state for the next loop iteration if resuming
#         if isinstance(current_state, Command):
#              pass # Pass the command directly
#         else:
#              current_state = None # Let the graph load state from checkpoint