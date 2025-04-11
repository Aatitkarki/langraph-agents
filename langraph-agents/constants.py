import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler
from pydantic import SecretStr

# Load environment variables from .env file
load_dotenv()

# --- API Configuration ---

# OpenAI Compatible Endpoint
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE","")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gemini/gemini-2.5-pro-exp-03-25")

# Tavily Search
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# LANGFUSE KEYS 
LANGFUSE_HOST=os.getenv("LANGFUSE_HOST", "")
LANGFUSE_PUBLIC_KEY=os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY=os.getenv("LANGFUSE_SECRET_KEY", "")

llm = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY),
    base_url=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
)
LANGFUSE_HANDLER = CallbackHandler(
    secret_key=LANGFUSE_SECRET_KEY,
    public_key=LANGFUSE_PUBLIC_KEY,
    host=LANGFUSE_HOST
)

# response = langfuse_handler.auth_check()

# --- Validation ---
# Basic check to ensure essential keys are loaded
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in .env file or environment variables.")
if not OPENAI_API_BASE:
    print("Warning: OPENAI_API_BASE not found. Using default OpenAI endpoint if applicable.")
if not TAVILY_API_KEY:
    print("Warning: TAVILY_API_KEY not found. Search tool functionality will be limited.")