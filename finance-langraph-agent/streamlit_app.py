import streamlit as st
import uuid
from openai import OpenAI # Keep OpenAI import for potential direct use or consistency
# Import the core agent execution function from your banking_agent file
from banking_agent import run_finance_query, OPENAI_API_KEY # Assuming OPENAI_API_KEY is handled similarly

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰")

# --- Sidebar for API Key ---
with st.sidebar:
    # Use the OPENAI_API_KEY from banking_agent if available, otherwise prompt
    st.session_state.openai_api_key = st.text_input(
        "OpenAI API Key",
        key="chatbot_api_key",
        type="password",
        value=OPENAI_API_KEY or "" # Pre-fill if found in env
    )
    if not st.session_state.openai_api_key and not OPENAI_API_KEY:
        st.warning("Please enter your OpenAI API Key to use the chatbot.")
    elif not st.session_state.openai_api_key and OPENAI_API_KEY:
         st.session_state.openai_api_key = OPENAI_API_KEY # Use env var if user clears input
         st.info("Using API Key from environment variables.")

    st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
    # Add links relevant to your project if desired
    # st.markdown("[View the source code](...)")

# --- Main Chat Interface ---
st.title("💰 Banking Agent Chatbot")
st.caption("🚀 Ask me about your accounts, transactions, cards, or exchange rates!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you today?"}]
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = f"streamlit_thread_{uuid.uuid4()}" # Unique thread ID per session

# Display chat messages from history on app rerun
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Accept user input
if prompt := st.chat_input("What would you like to ask?"):
    # Check for API key before proceeding
    if not st.session_state.openai_api_key:
        st.info("Please add your OpenAI API key in the sidebar to continue.")
        st.stop()

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display thinking indicator
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call the banking agent function
            try:
                response = run_finance_query(
                    query=prompt,
                    thread_id=st.session_state.thread_id,
                    openai_api_key=st.session_state.openai_api_key # Pass the key
                )
                msg_content = response
            except Exception as e:
                st.error(f"An error occurred: {e}")
                msg_content = "Sorry, I encountered an error. Please try again."

            # Display assistant response
            st.markdown(msg_content)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": msg_content})