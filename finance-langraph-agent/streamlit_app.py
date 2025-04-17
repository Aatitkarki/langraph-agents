import logging
import streamlit as st
import uuid
import os
import tempfile
import time # For potential delays/feedback

# Import the core agent execution function and API key constant from the new structure
from src.main import run_single_query
from src.utils.llm_config import OPENAI_API_KEY # Default key from env
from src.utils.logging_config import setup_logging
# Import RAG loading functions
from src.utils.load_vector_data import setup_vector_store, load_pdf_to_vector_store

# --- Streamlit Page Configuration ---
st.set_page_config(page_title="Banking Agent Chatbot", page_icon="💰", layout="wide")

# Configure logging early
# Consider moving level to env var or config file later
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Session State Initialization ---
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you today?"}]
# Initialize thread ID for conversation memory
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = f"streamlit_thread_{uuid.uuid4()}"
# Initialize API key in session state, allow override via sidebar
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = OPENAI_API_KEY # Load from env var initially or None

# --- Sidebar for Configuration and Upload ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Input (Allow override)
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="Paste key here if not set in environment",
        help="Required for the chatbot and PDF embedding.",
        value=st.session_state.openai_api_key or "" # Display current key from session state
    )
    # Update session state if user provides input and it's different
    if api_key_input and api_key_input != st.session_state.openai_api_key:
        st.session_state.openai_api_key = api_key_input
        st.success("API Key updated for this session.")
        # Set environment variable as well, as backend might rely on it
        os.environ["OPENAI_API_KEY"] = api_key_input
        logger.info("OpenAI API Key updated in session and environment.")


    st.divider()

    st.header("📚 Upload PDF to Knowledge Base")
    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type="pdf",
        accept_multiple_files=False, # Process one file at a time for simplicity
        key="pdf_uploader" # Add a key to manage state
    )

    if uploaded_file is not None:
        # Check if API key is available before allowing processing
        if not st.session_state.openai_api_key:
            st.warning("Please enter your OpenAI API key above before processing the PDF.")
        else:
            # Use a button to trigger processing after upload
            if st.button(f"Process '{uploaded_file.name}'"):
                processing_success = False # Flag to track outcome
                tmp_file_path = None # Ensure variable exists
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        # 1. Ensure API key is set in environment for backend
                        if not os.environ.get("OPENAI_API_KEY"):
                             os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
                             logger.info("Temporarily set OPENAI_API_KEY in environment for processing.")

                        # 2. Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name
                        logger.info(f"Saved temporary file: {tmp_file_path}")

                        # 3. Setup Vector Store Connection
                        st.info("Connecting to vector store...")
                        time.sleep(0.5) # Small delay for user feedback
                        vector_store = setup_vector_store() # Assumes DB connection details are in env vars

                        # 4. Load PDF content into the store
                        st.info(f"Loading '{uploaded_file.name}' into knowledge base...")
                        time.sleep(0.5)
                        processing_success = load_pdf_to_vector_store(vector_store, tmp_file_path)

                        if processing_success:
                            st.success(f"✅ Successfully added '{uploaded_file.name}' to the knowledge base!")
                            # Optionally clear the uploader state here if needed,
                            # though Streamlit often handles this reasonably well.
                        else:
                            st.error(f"⚠️ Failed to process '{uploaded_file.name}'. Check application logs for details.")

                    except Exception as e:
                        st.error(f"❌ An error occurred during PDF processing: {e}")
                        logger.error(f"PDF Processing Error: {e}", exc_info=True)
                    finally:
                        # 5. Clean up temporary file
                        if tmp_file_path and os.path.exists(tmp_file_path):
                            try:
                                os.remove(tmp_file_path)
                                logger.info(f"Cleaned up temporary file: {tmp_file_path}")
                            except Exception as e_clean:
                                logger.error(f"Error cleaning up temp file {tmp_file_path}: {e_clean}")

# --- Main Chat Interface ---
st.title("💰 Banking Agent Chatbot")
st.caption("🚀 Ask me about your accounts, transactions, cards, or exchange rates! You can also upload PDFs via the sidebar.")

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accept user input
if prompt := st.chat_input("What would you like to ask?"):
    # Check for API key before proceeding
    if not st.session_state.openai_api_key:
        st.warning("Please add your OpenAI API key in the sidebar to continue.")
        st.stop() # Stop execution if no key

    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display thinking indicator and call agent
    with st.spinner("Thinking..."):
        try:
            # Ensure the API key is explicitly set in the environment for the backend process
            # This is crucial if the backend relies on os.environ instead of passed config
            if not os.environ.get("OPENAI_API_KEY") and st.session_state.openai_api_key:
                 os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
                 logger.info("Temporarily set OPENAI_API_KEY in environment for query.")

            response = run_single_query(
                query=prompt,
                thread_id=st.session_state.thread_id,
                openai_api_key=st.session_state.openai_api_key # Pass for potential direct use if needed
            )
            msg_content = response
        except Exception as e:
            logger.error(f"Error running query '{prompt}': {e}", exc_info=True)
            st.error(f"An error occurred: {e}") # Show error in chat UI
            msg_content = "Sorry, I encountered an error processing your request."

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(msg_content)
    # Add assistant response to session state
    st.session_state.messages.append({"role": "assistant", "content": msg_content})