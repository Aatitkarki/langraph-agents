
import os

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE","")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")

LLM = ChatOpenAI(
    api_key=SecretStr(OPENAI_API_KEY),
    base_url=OPENAI_API_BASE,
    model=OPENAI_MODEL_NAME
) 

