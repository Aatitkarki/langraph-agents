# langgraph_usecases/debate_simulator.py
from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
# from langchain_anthropic import ChatAnthropic # Example model

# --- State Definition ---
class DebateState(TypedDict):
    """Represents the state of the debate."""
    topic: str
    # Use add_messages for conversation history
    messages: Annotated[List[BaseMessage], add_messages]
    # Track whose turn it is
    turn: Literal["Moderator", "Proponent", "Opponent", "END"]
    # Optional: Track arguments or points made
    proponent_points: List[str]
    opponent_points: List[str]

# --- Model Initialization (Placeholder) ---
# model = ChatAnthropic(model="claude-3-5-sonnet-20240620") # Replace with actual model

# --- Agent Node Functions (Placeholders) ---

def moderator_agent(state: DebateState) -> dict:
    """
    Moderator agent: Sets the topic, manages turns, summarizes, and decides when to end.
    """
    print("---MODERATOR---")
    current_messages = state['messages']
    last_speaker = state.get('turn', START) # Get the last speaker or START

    # Initial turn: Introduce topic
    if last_speaker == START:
        topic = state['topic']
        text = f"Welcome! Today's debate topic is: {topic}. Let's start with the Proponent."
        next_turn = "Proponent"
    # After Proponent speaks
    elif last_speaker == "Proponent":
        # Placeholder logic: Ask Opponent to respond
        text = "Thank you, Proponent. Opponent, your response?"
        next_turn = "Opponent"
    # After Opponent speaks
    elif last_speaker == "Opponent":
         # Placeholder logic: Decide if debate continues or ends (e.g., after N turns)
        if len(current_messages) > 6: # Example end condition
             text = "This concludes our debate. Thank you both."
             next_turn = "END"
        else:
             text = "Thank you, Opponent. Proponent, your rebuttal?"
             next_turn = "Proponent"
    else: # Should not happen in this simple flow
        text = "Let's wrap up."
        next_turn = "END"

    print(f"Moderator says: {text}")
    # Return message and next turn
    return {"messages": [AIMessage(content=text, name="Moderator")], "turn": next_turn}


def proponent_agent(state: DebateState) -> dict:
    """
    Proponent agent: Argues in favor of the topic.
    """
    print("---PROPONENT---")
    topic = state['topic']
    current_messages = state['messages']
    # Placeholder logic: Generate argument (LLM call)
    argument = f"As the proponent, I believe {topic} is beneficial because... [Reason P{len(state.get('proponent_points', [])) + 1}]"
    print(f"Proponent argues: {argument}")
    # Update points and return message + next turn (back to Moderator)
    new_points = state.get('proponent_points', []) + [argument]
    return {"messages": [AIMessage(content=argument, name="Proponent")], "turn": "Moderator", "proponent_points": new_points}

def opponent_agent(state: DebateState) -> dict:
    """
    Opponent agent: Argues against the topic.
    """
    print("---OPPONENT---")
    topic = state['topic']
    current_messages = state['messages']
    # Placeholder logic: Generate counter-argument (LLM call)
    argument = f"As the opponent, I argue that {topic} has drawbacks such as... [Reason O{len(state.get('opponent_points', [])) + 1}]"
    print(f"Opponent argues: {argument}")
    # Update points and return message + next turn (back to Moderator)
    new_points = state.get('opponent_points', []) + [argument]
    return {"messages": [AIMessage(content=argument, name="Opponent")], "turn": "Moderator", "opponent_points": new_points}

# --- Routing Function ---
def route_debate(state: DebateState) -> Literal["Moderator", "Proponent", "Opponent", "__end__"]:
    """Routes control to the agent whose turn it is."""
    next_turn = state.get("turn")
    print(f"Routing to: {next_turn}")
    if next_turn == "END":
        return END
    elif next_turn == "Proponent":
        return "Proponent"
    elif next_turn == "Opponent":
        return "Opponent"
    else: # Default or after agents speak, go back to Moderator
        return "Moderator"

# --- Graph Definition ---
debate_workflow = StateGraph(DebateState)

# Add nodes
debate_workflow.add_node("Moderator", moderator_agent)
debate_workflow.add_node("Proponent", proponent_agent)
debate_workflow.add_node("Opponent", opponent_agent)

# Add entry point
debate_workflow.add_edge(START, "Moderator") # Start with the Moderator

# Add routing edges
debate_workflow.add_conditional_edges(
    "Moderator",
    route_debate,
    {
        "Proponent": "Proponent",
        "Opponent": "Opponent",
        END: END
    }
)
# After Proponent/Opponent speak, they always go back to the Moderator
debate_workflow.add_edge("Proponent", "Moderator")
debate_workflow.add_edge("Opponent", "Moderator")

# --- Compile the Graph ---
debate_simulator_agent = debate_workflow.compile()

# Example Invocation (Conceptual)
# if __name__ == "__main__":
#     from langgraph.checkpoint.memory import MemorySaver
#     memory = MemorySaver()
#     config = {"configurable": {"thread_id": "debate-1"}}
#     initial_state = {
#         "topic": "The future of AI in education",
#         "messages": [],
#         "proponent_points": [],
#         "opponent_points": [],
#     }
#     for event in debate_simulator_agent.stream(initial_state, config=config):
#         # Print messages or specific state updates
#         if "messages" in event.get("Moderator", {}):
#             print("Moderator:", event["Moderator"]["messages"][-1].content)
#         if "messages" in event.get("Proponent", {}):
#             print("Proponent:", event["Proponent"]["messages"][-1].content)
#         if "messages" in event.get("Opponent", {}):
#             print("Opponent:", event["Opponent"]["messages"][-1].content)
#         print("---")