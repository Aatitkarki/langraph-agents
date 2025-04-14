import streamlit as st
import uuid
import asyncio # Add asyncio
# Import the core agent execution function and API key constant from the new structure
from src.main import run_finance_query
from src.utils.llm_config import OPENAI_API_KEY # API Key loaded from env vars

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰")

# --- Sidebar for API Key ---
with st.sidebar:
    # Use the OPENAI_API_KEY from src.utils.llm_config (env var) if available, otherwise prompt
    st.session_state.openai_api_key = st.text_input(
        "OpenAI API Key",
        key="chatbot_api_key",
        type="password",
        value=OPENAI_API_KEY or "" # Pre-fill if found in env (from src.utils.llm_config)
    )
    if not st.session_state.openai_api_key and not OPENAI_API_KEY: # Check against key from src.utils.llm_config
        st.warning("Please enter your OpenAI API Key to use the chatbot.")
    elif not st.session_state.openai_api_key and OPENAI_API_KEY: # Check against key from src.utils.llm_config
         st.session_state.openai_api_key = OPENAI_API_KEY # Use env var (from src.utils.llm_config) if user clears input
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

    # Display assistant response with streaming
    with st.chat_message("assistant"):
        # Use st.write_stream which handles async generators
        try:
            # Define the async generator function to pass to write_stream
            # This wrapper is needed because write_stream expects the generator directly
            async def stream_response():
                full_response = ""
                assert prompt is not None # Assure type checker prompt is a string here
                async for chunk in run_finance_query(
                    query=prompt,
                    thread_id=st.session_state.thread_id,
                    openai_api_key=st.session_state.openai_api_key
                ):
                    yield chunk # Yield each part to Streamlit for display
                    full_response += chunk # Accumulate the full response

                # Store the complete message in session state *after* the stream finishes
                # We need to find a way to get this back out or store it differently.
                # Let's store it temporarily and add it after the stream.
                st.session_state.temp_full_response = full_response


            # Run the stream and display it
            st.session_state.temp_full_response = None # Reset before stream
            st.write_stream(stream_response)

            # Retrieve the full response stored by the wrapper and add to history
            if st.session_state.temp_full_response:
                 st.session_state.messages.append({"role": "assistant", "content": st.session_state.temp_full_response})
                 del st.session_state.temp_full_response # Clean up temp storage
            else:
                 # Handle cases where the stream might have ended abruptly or with error message already yielded
                 # Check the last message added by the stream itself if needed
                 if not st.session_state.messages[-1]["content"].startswith("An error occurred"):
                     st.session_state.messages.append({"role": "assistant", "content": "Processing complete."}) # Fallback message


        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {e}"})