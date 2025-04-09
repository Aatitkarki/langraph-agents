import streamlit as st
import os
import re
from operator import itemgetter
from typing import Dict, Any, TypedDict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

# --- Constants ---
AGENT_A_NAME = "Alex, the Logical Analyst"
AGENT_B_NAME = "Blake, the Empathetic Advocate"
JUDGE_NAME = "JusticeBot"
DEBATE_TOPIC = "Artificial Intelligence should be heavily regulated by governments."
MAX_ROUNDS = 3
LLM_MODEL = "deepseek-chat" # Make sure you have access and credits for this model

# --- Helper Functions ---



def get_openai_api_key():
    """Gets the OpenAI API key from Streamlit secrets or environment variables."""
    # api_key = os.environ.get("API_KEY")
    # if not api_key:
    #     st.error("OpenAI API key not found. Please set it in Streamlit secrets (OPENAI_API_KEY) or as an environment variable.")
    #     st.stop()
    # return api_key
    return "sk-4lTjud-99nWlgejCsxLXYQ"

def parse_judge_scores(text: str) -> Dict[str, int]:
    """Parses the judge's text output to extract scores."""
    scores = {
        f"{AGENT_A_NAME}_clarity": 0, f"{AGENT_A_NAME}_evidence": 0, f"{AGENT_A_NAME}_persuasiveness": 0, f"{AGENT_A_NAME}_rebuttal": 0,
        f"{AGENT_B_NAME}_clarity": 0, f"{AGENT_B_NAME}_evidence": 0, f"{AGENT_B_NAME}_persuasiveness": 0, f"{AGENT_B_NAME}_rebuttal": 0,
    }
    
    # More robust regex to find scores, handling potential variations
    patterns = {
        f"{AGENT_A_NAME}_clarity": rf"{re.escape(AGENT_A_NAME)}.*?Clarity.*?(\d+)/5",
        f"{AGENT_A_NAME}_evidence": rf"{re.escape(AGENT_A_NAME)}.*?Evidence.*?(\d+)/5",
        f"{AGENT_A_NAME}_persuasiveness": rf"{re.escape(AGENT_A_NAME)}.*?Persuasiveness.*?(\d+)/5",
        f"{AGENT_A_NAME}_rebuttal": rf"{re.escape(AGENT_A_NAME)}.*?Rebuttal.*?(\d+)/5",
        f"{AGENT_B_NAME}_clarity": rf"{re.escape(AGENT_B_NAME)}.*?Clarity.*?(\d+)/5",
        f"{AGENT_B_NAME}_evidence": rf"{re.escape(AGENT_B_NAME)}.*?Evidence.*?(\d+)/5",
        f"{AGENT_B_NAME}_persuasiveness": rf"{re.escape(AGENT_B_NAME)}.*?Persuasiveness.*?(\d+)/5",
        f"{AGENT_B_NAME}_rebuttal": rf"{re.escape(AGENT_B_NAME)}.*?Rebuttal.*?(\d+)/5",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                scores[key] = int(match.group(1))
            except (ValueError, IndexError):
                print(f"Warning: Could not parse score for {key} from judge output.") # Log warning

    return scores

# --- LangGraph State Definition ---

class DebateState(TypedDict):
    """Represents the state of the debate."""
    topic: str
    messages: List[BaseMessage]
    agent_a_score: int
    agent_b_score: int
    current_round: int
    max_rounds: int
    last_speaker: Optional[str]
    error: Optional[str]
    judge_feedback: Optional[str] # Temporary storage for judge feedback text

# --- Agent Definitions ---

def create_agent_runnable(llm: ChatOpenAI, system_prompt: str):
    """Creates a runnable chain for an agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    return prompt | llm

# --- LangGraph Nodes ---

def agent_a_node(state: DebateState):
    """Represents Agent A's turn."""
    st.write(f"--- {AGENT_A_NAME}'s Turn (Round {state['current_round']}) ---")
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7, api_key=get_openai_api_key(),base_url="https://litellm.sureshk.com.np/v1")

    system_prompt = f"""You are {AGENT_A_NAME}, a debater with a Logical personality.
Your goal is to argue FOR the topic: "{state['topic']}".
You must provide well-reasoned arguments, cite plausible (even if fabricated) evidence, and effectively counter the opponent's points if they have spoken.
Keep your response focused on the debate topic. Address the previous speaker's points directly if applicable.
Analyze the conversation history and make your next point. Be logical and clear.
Conversation History:
{state['messages']}"""

    agent_a_runnable = create_agent_runnable(llm, system_prompt)

    try:
        response = agent_a_runnable.invoke({"messages": state["messages"]})
        if isinstance(response, AIMessage):
            message_content = response.content
        else:
             raise TypeError(f"Expected AIMessage, got {type(response)}")

        # Ensure it's a non-empty string
        if not message_content or not isinstance(message_content, str):
             raise ValueError("Agent A generated an empty or invalid response.")

        st.session_state.latest_agent_a_response = message_content # Store for display
        return {
            "messages": [AIMessage(content=message_content, name=AGENT_A_NAME)],
            "last_speaker": AGENT_A_NAME
        }
    except Exception as e:
        st.error(f"Error during Agent A's turn: {e}")
        return {"error": f"Agent A failed: {e}", "last_speaker": AGENT_A_NAME} # Pass error state

def agent_b_node(state: DebateState):
    """Represents Agent B's turn."""
    st.write(f"--- {AGENT_B_NAME}'s Turn (Round {state['current_round']}) ---")
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.7, api_key=get_openai_api_key(),base_url="https://litellm.sureshk.com.np/v1")

    system_prompt = f"""You are {AGENT_B_NAME}, a debater with a Persuasive personality.
Your goal is to argue AGAINST the topic: "{state['topic']}".
You must provide well-reasoned arguments, cite plausible (even if fabricated) evidence, and effectively counter the opponent's points ({AGENT_A_NAME}'s last statement).
Keep your response focused on the debate topic. Address the previous speaker's points directly.
Analyze the conversation history and make your next point. Be persuasive and empathetic where appropriate.
Conversation History:
{state['messages']}"""

    agent_b_runnable = create_agent_runnable(llm, system_prompt)

    try:
        response = agent_b_runnable.invoke({"messages": state["messages"]})

        if isinstance(response, AIMessage):
             message_content = response.content
        else:
             raise TypeError(f"Expected AIMessage, got {type(response)}")

        # Ensure it's a non-empty string
        if not message_content or not isinstance(message_content, str):
             raise ValueError("Agent B generated an empty or invalid response.")

        st.session_state.latest_agent_b_response = message_content # Store for display
        return {
            "messages": [AIMessage(content=message_content, name=AGENT_B_NAME)],
            "last_speaker": AGENT_B_NAME
        }
    except Exception as e:
        st.error(f"Error during Agent B's turn: {e}")
        return {"error": f"Agent B failed: {e}", "last_speaker": AGENT_B_NAME} # Pass error state


def judge_node(state: DebateState):
    """Represents the Judge's turn to evaluate the round."""
    st.write(f"--- {JUDGE_NAME}'s Turn (Evaluating Round {state['current_round']}) ---")
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.3, api_key=get_openai_api_key(),base_url="https://litellm.sureshk.com.np/v1")

    # Get the last two messages (A's argument and B's rebuttal for this round)
    last_two_messages = state['messages'][-2:]
    agent_a_msg = next((msg for msg in reversed(last_two_messages) if msg.name == AGENT_A_NAME), None)
    agent_b_msg = next((msg for msg in reversed(last_two_messages) if msg.name == AGENT_B_NAME), None)

    if not agent_a_msg or not agent_b_msg:
         st.warning("Judge could not find both agent messages for this round. Skipping scoring.")
         # Still increment round, but don't score
         return {"current_round": state["current_round"] + 1, "judge_feedback": "Evaluation skipped due to missing arguments."}


    judge_prompt = f"""You are {JUDGE_NAME}, an impartial judge evaluating a debate round on the topic: "{state['topic']}".
You need to evaluate the arguments presented by {AGENT_A_NAME} (arguing FOR) and {AGENT_B_NAME} (arguing AGAINST) in the *latest exchange*.

**{AGENT_A_NAME}'s Argument:**
{agent_a_msg.content}

**{AGENT_B_NAME}'s Rebuttal/Argument:**
{agent_b_msg.content}

**Evaluation Criteria:**
For EACH agent, provide scores from 0 to 5 for the following:
1.  **Clarity:** How clearly the argument was presented. (0-5)
2.  **Evidence:** The strength and relevance of the evidence provided (even if fabricated, assess its plausibility and usage). (0-5)
3.  **Persuasiveness:** How convincing the argument was. (0-5)
4.  **Rebuttal:** How effectively the agent addressed and countered the *opponent's previous points* (if applicable in this turn). (0-5)

**Output Format:**
Provide a brief justification for your scores for *each* agent, followed by the scores in a clear format. Example:

**{AGENT_A_NAME} Evaluation:**
[Justification for Alex's scores...]
Scores: Clarity: X/5, Evidence: Y/5, Persuasiveness: Z/5, Rebuttal: W/5

**{AGENT_B_NAME} Evaluation:**
[Justification for Blake's scores...]
Scores: Clarity: A/5, Evidence: B/5, Persuasiveness: C/5, Rebuttal: D/5
"""

    try:
        response = llm.invoke([HumanMessage(content=judge_prompt)])
        if isinstance(response, AIMessage):
            judge_response_text = response.content
        else:
            raise TypeError(f"Expected AIMessage from Judge, got {type(response)}")

        if not judge_response_text or not isinstance(judge_response_text, str):
             raise ValueError("Judge generated an empty or invalid response.")

        st.session_state.latest_judge_feedback = judge_response_text # Store for display

        # Parse scores
        scores = parse_judge_scores(judge_response_text)
        agent_a_round_score = sum(scores[k] for k in scores if k.startswith(AGENT_A_NAME))
        agent_b_round_score = sum(scores[k] for k in scores if k.startswith(AGENT_B_NAME))

        return {
            "messages": [AIMessage(content=judge_response_text, name=JUDGE_NAME)],
            "agent_a_score": state["agent_a_score"] + agent_a_round_score,
            "agent_b_score": state["agent_b_score"] + agent_b_round_score,
            "current_round": state["current_round"] + 1,
            "last_speaker": JUDGE_NAME,
            "judge_feedback": judge_response_text # Keep the full text
        }
    except Exception as e:
        st.error(f"Error during Judge's turn: {e}")
        # Still increment round maybe? Or halt? Let's increment but flag error.
        return {
            "error": f"Judge failed: {e}",
            "current_round": state["current_round"] + 1, # Increment round even on failure
            "last_speaker": JUDGE_NAME,
            "judge_feedback": f"Error during evaluation: {e}"
        }


# --- LangGraph Conditional Edge ---

def should_continue(state: DebateState):
    """Determines whether the debate should continue."""
    if state.get("error"): # Stop if any node reported an error
        st.error(f"Halting debate due to error: {state['error']}")
        return END
    if state["current_round"] > state["max_rounds"]:
        st.success("Debate finished!")
        return END
    else:
        # Alternate starting speaker each round after the first
        if state["current_round"] % 2 == 1: # Round 1, 3, 5... Agent A starts
             return "agent_a_turn"
        else: # Round 2, 4, 6... Agent B starts
             return "agent_b_turn"
        # Note: Original request implied A->B->Judge always. This alternates start.
        # If strict A->B->Judge is needed, always return "agent_a_turn" here.
        # Let's stick to A->B->Judge for simplicity as per initial request structure.
        # return "agent_a_turn" # Keep A -> B -> Judge flow strict

# --- Build the Graph ---

def build_graph():
    """Builds the LangGraph StateGraph."""
    workflow = StateGraph(DebateState)

    # Add nodes
    workflow.add_node("agent_a_turn", agent_a_node)
    workflow.add_node("agent_b_turn", agent_b_node)
    workflow.add_node("judge_turn", judge_node)

    # Set entry point
    workflow.set_entry_point("agent_a_turn")

    # Add edges
    workflow.add_edge("agent_a_turn", "agent_b_turn")
    workflow.add_edge("agent_b_turn", "judge_turn")

    # Add conditional edge after judge's turn
    workflow.add_conditional_edges(
        "judge_turn",
        should_continue,
        {
            "agent_a_turn": "agent_a_turn", # Loop back to Agent A for next round
            END: END,
        },
    )

    # Compile the graph - REMOVED recursion_limit
    app = workflow.compile(checkpointer=None)
    return app

# --- Streamlit UI ---

st.set_page_config(layout="wide", page_title="AI Debate Competition")

st.title("🏆 AI Debate Competition 🏆")

# Get API Key at the start
openai_api_key = get_openai_api_key() # Ensures key exists before proceeding

st.header(f"Debate Topic: {DEBATE_TOPIC}")

# Initialize session state
if 'graph_app' not in st.session_state:
    st.session_state.graph_app = build_graph()
    st.session_state.debate_state = DebateState(
        topic=DEBATE_TOPIC,
        messages=[],
        agent_a_score=0,
        agent_b_score=0,
        current_round=1,
        max_rounds=MAX_ROUNDS,
        last_speaker=None,
        error=None,
        judge_feedback=None
    )
    st.session_state.debate_history = [] # Separate list to store display messages
    st.session_state.running = False
    st.session_state.latest_agent_a_response = ""
    st.session_state.latest_agent_b_response = ""
    st.session_state.latest_judge_feedback = ""


# --- Display Area ---
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"🟢 {AGENT_A_NAME} (FOR)")
    st.metric("Score", st.session_state.debate_state.get('agent_a_score', 0))
with col2:
    st.subheader(f"🔴 {AGENT_B_NAME} (AGAINST)")
    st.metric("Score", st.session_state.debate_state.get('agent_b_score', 0))

st.markdown("---")
st.info(f"Round {st.session_state.debate_state.get('current_round', 1)} of {MAX_ROUNDS}")
st.markdown("---")

# Debate Log Placeholder
log_placeholder = st.container() # Use a container for the log

def display_debate_log():
    """Displays the formatted debate history."""
    with log_placeholder:
        st.empty() # Clear previous log entries
        st.subheader("Debate Log")
        for msg_info in st.session_state.debate_history:
            speaker = msg_info["speaker"]
            content = msg_info["content"]
            round_num = msg_info.get("round")

            icon = "❓"
            if speaker == AGENT_A_NAME: icon = "🟢"
            elif speaker == AGENT_B_NAME: icon = "🔴"
            elif speaker == JUDGE_NAME: icon = "⚖️"

            with st.chat_message(name=speaker, avatar=icon):
                 if round_num:
                     st.markdown(f"**Round {round_num}**")
                 st.markdown(content) # Use markdown for potential formatting in agent responses

# Initial display
display_debate_log()

# --- Control Buttons ---
control_cols = st.columns([1, 1, 5]) # Adjust column widths as needed

with control_cols[0]:
    start_button_label = "Start Debate" if not st.session_state.debate_history else "Next Step"
    if st.button(start_button_label, disabled=st.session_state.running):
        st.session_state.running = True
        st.rerun() # Rerun to disable button and show spinner

with control_cols[1]:
     if st.button("Reset Debate", type="secondary"):
         # Clear relevant session state keys
         keys_to_reset = ['graph_app', 'debate_state', 'debate_history', 'running',
                          'latest_agent_a_response', 'latest_agent_b_response', 'latest_judge_feedback']
         for key in keys_to_reset:
             if key in st.session_state:
                 del st.session_state[key]
         st.rerun() # Rerun to re-initialize

# --- LangGraph Execution Logic ---
if st.session_state.running:
    graph_app = st.session_state.graph_app
    current_state = st.session_state.debate_state

    # Determine the next step based on last speaker or if it's the start
    last_speaker = current_state.get('last_speaker')
    current_round = current_state.get('current_round', 1)

    next_step_input = current_state.copy() # Pass the current state to the next step

    st.write("Executing next step...")
    spinner_msg = "Thinking..."
    if last_speaker == AGENT_A_NAME: spinner_msg = f"{AGENT_B_NAME} is preparing rebuttal..."
    elif last_speaker == AGENT_B_NAME: spinner_msg = f"{JUDGE_NAME} is evaluating..."
    elif last_speaker == JUDGE_NAME: spinner_msg = f"{AGENT_A_NAME} is preparing for Round {current_round}..."
    elif not last_speaker: spinner_msg = f"{AGENT_A_NAME} is starting the debate..."


    with st.spinner(spinner_msg):
        try:
            # Stream the graph execution - processes one node at a time
            # Use invoke for simplicity first, stream is better for responsiveness
            # for step_output in graph_app.stream(next_step_input, {"recursion_limit": 15}):
            #     # step_output is a dict where keys are node names and values are their output
            #     node_name = list(step_output.keys())[0]
            #     node_output = step_output[node_name]
            #     print(f"Completed node: {node_name}") # Debug print

            #     # Update the central state - crucial step
            #     current_state.update(node_output) # Update with the output of the completed node

            # Let's use invoke for now to make state management simpler for this example
            final_state = None
            # We need to run the graph until it hits a breakpoint or END
            # LangGraph's invoke/stream runs the *entire* graph until END or interruption
            # For step-by-step, we'd need a different approach (e.g., manually calling nodes or using checkpoints)
            # Let's run one full A->B->Judge cycle per button click for this UI

            # This logic needs refinement. Let's run the graph and see where it ends.
            # The graph will run until END or the next input is required (not applicable here)
            # So, one click will run the *whole* debate. This isn't ideal for interactive display.

            # --- Revised Approach: Simulate Step-by-Step Execution ---
            # We'll manually determine which node to call next based on state.
            # This deviates slightly from pure LangGraph stream/invoke but gives UI control.

            next_node = None
            if not last_speaker: # Start of the debate
                next_node = "agent_a_turn"
            elif last_speaker == AGENT_A_NAME:
                next_node = "agent_b_turn"
            elif last_speaker == AGENT_B_NAME:
                next_node = "judge_turn"
            elif last_speaker == JUDGE_NAME:
                if current_round <= MAX_ROUNDS:
                    next_node = "agent_a_turn" # Start next round
                else:
                    st.success("Debate Finished!")
                    st.session_state.running = False
                    st.rerun()


            if next_node:
                node_function = None
                if next_node == "agent_a_turn": node_function = agent_a_node
                elif next_node == "agent_b_turn": node_function = agent_b_node
                elif next_node == "judge_turn": node_function = judge_node

                if node_function:
                     print(f"Executing node: {next_node}")
                     node_output = node_function(current_state)

                     # Update state
                     current_state.update(node_output)

                     # Append new message(s) to history for display
                     new_messages = node_output.get("messages", [])
                     speaker_name = node_output.get("last_speaker", "System") # Get speaker from node output

                     if speaker_name == AGENT_A_NAME:
                        st.session_state.debate_history.append({"speaker": speaker_name, "content": st.session_state.latest_agent_a_response, "round": current_round})
                     elif speaker_name == AGENT_B_NAME:
                        st.session_state.debate_history.append({"speaker": speaker_name, "content": st.session_state.latest_agent_b_response, "round": current_round})
                     elif speaker_name == JUDGE_NAME:
                         # Display Judge's feedback immediately
                         judge_feedback_text = current_state.get('judge_feedback', 'No feedback provided.')
                         st.session_state.debate_history.append({"speaker": speaker_name, "content": judge_feedback_text, "round": current_round -1}) # Judge evaluates previous round


                     # Update the main session state
                     st.session_state.debate_state = current_state

                     # Check for errors after node execution
                     if current_state.get("error"):
                         st.error(f"Error encountered: {current_state['error']}")
                         st.session_state.running = False
                     # Check if the debate should end after the judge's turn
                     elif speaker_name == JUDGE_NAME and current_state["current_round"] > MAX_ROUNDS:
                         st.success("Debate finished after final evaluation!")
                         st.session_state.running = False


                else:
                    st.error("Could not determine next step function.")
                    st.session_state.running = False


        except Exception as e:
            st.error(f"An unexpected error occurred during graph execution: {e}")
            import traceback
            st.code(traceback.format_exc()) # Print traceback for debugging
            st.session_state.running = False # Stop execution on error

        # Rerun Streamlit to update the UI with the new state and log
        # Check if we should continue running or stop
        if st.session_state.running: # Only rerun if not stopped by error or end condition
            # Small delay to allow user to see spinner/message
            # time.sleep(0.5) # Optional delay
             pass # Rerun happens at the end of the script anyway if state changed
        # Reset running flag if it wasn't already turned off by end condition/error
        # else:
        #     st.session_state.running = False # Explicitly ensure it's off if loop finishes early

    # This rerun updates the display *after* the spinner block completes
    st.session_state.running = False # Reset running state for next button press
    st.rerun()


# Final state display if debate ended
if st.session_state.debate_state.get('current_round', 1) > MAX_ROUNDS and not st.session_state.running:
     st.balloons()
     st.success("Debate Concluded!")
     final_a_score = st.session_state.debate_state.get('agent_a_score', 0)
     final_b_score = st.session_state.debate_state.get('agent_b_score', 0)
     winner = "It's a tie!"
     if final_a_score > final_b_score:
         winner = f"{AGENT_A_NAME} wins!"
     elif final_b_score > final_a_score:
         winner = f"{AGENT_B_NAME} wins!"
     st.header(f"Final Result: {winner}")
