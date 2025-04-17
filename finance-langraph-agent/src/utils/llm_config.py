import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()

# --- LLM Configuration ---
# Load API keys and model details from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
OPENAI_MODEL_NAME = os.getenv("LLAMA3.2", "")
SUPERVISOR_MODEL_NAME = os.getenv("COGITO8B", "")

# Instantiate the LLM
# Ensure API key is provided either via environment or other means (e.g., Streamlit input)
llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None, # Handle case where key might be empty initially
    base_url=OPENAI_API_BASE if OPENAI_API_BASE else None,
    model=OPENAI_MODEL_NAME if OPENAI_MODEL_NAME else "" # Default model if not specified
)

supervisor_llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None, # Handle case where key might be empty initially
    base_url=OPENAI_API_BASE if OPENAI_API_BASE else None,
    model=SUPERVISOR_MODEL_NAME if SUPERVISOR_MODEL_NAME else "" # Default model if not specified
)



# Note: The Streamlit app might override the api_key later based on user input.
# This setup primarily relies on environment variables.