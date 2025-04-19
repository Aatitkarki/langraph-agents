# RAG (Retrieval-Augmented Generation) Implementation Details

This document explains how the RAG feature has been integrated into the financial agent application.

## Overview

The RAG feature allows the application to retrieve relevant information from a local knowledge base (a collection of PDF documents) and provide it as context to the agents. This helps agents answer more general questions related to finance, supplementing their specific tool-based capabilities.

## Workflow

1.  **Knowledge Base:**

    - A directory named `knowledge_base` is expected in the project's root directory.
    - Place any relevant PDF documents (e.g., financial guides, FAQs, policy documents) into this directory.

2.  **Indexing (Startup):**

    - When the application starts, the `create_supervisor_finance` function in `src/graph/supervisor.py` calls `build_rag_pipeline` from `src/utils/rag_utils.py`.
    - `build_rag_pipeline`:
      - Checks if a pre-built vector store index exists at `vector_store/faiss_index`.
      - **If the index doesn't exist or `force_recreate` is True:**
        - It loads all PDF files from the `knowledge_base` directory using `PyPDFLoader`.
        - Splits the loaded documents into smaller, manageable chunks using `RecursiveCharacterTextSplitter`.
        - Generates embeddings for each chunk using `OpenAIEmbeddings` (requires the `OPENAI_API_KEY` environment variable).
        - Creates a FAISS vector store index from these embeddings.
        - Saves the index locally to `vector_store/faiss_index` for future use.
      - **If the index exists:**
        - It loads the existing FAISS index directly from `vector_store/faiss_index`.

3.  **Retrieval (During Conversation):**

    - Inside the `supervisor_node` function (`src/graph/supervisor.py`):
    - When a new message from the user arrives, the supervisor checks if the vector store was successfully loaded/created.
    - If the vector store exists, the user's query (`latest_message.content`) is used to search the FAISS index via `retrieve_documents` (`src/utils/rag_utils.py`).
    - This function retrieves the top `k` (currently 3) most relevant document chunks based on semantic similarity.

4.  **Context Injection:**

    - The content of the retrieved document chunks is formatted into a single string.
    - This string is added to the `FinancialAgentState` under the key `rag_context`.

5.  **Agent Invocation:**

    - The supervisor routes the task to the appropriate worker agent (e.g., `account_agent`).
    - The agent runnables (defined in `src/agents/*.py`) are now created using a dynamic `ChatPromptTemplate`.
    - This template accesses the `rag_context` from the input state dictionary.
    - The `finance_agent_system_prompt` function (`src/agents/prompts.py`) receives this context.

6.  **Agent Response:**
    - The system prompt presented to the agent's LLM now includes the retrieved `rag_context` (if any was found).
    - The prompt instructs the agent to use this context to inform its response for general questions, while still prioritizing its specific tools for direct tasks.
    - The agent generates a response, potentially incorporating information from the retrieved documents alongside results from its tools.

## Key Files Modified

- `requirements.txt`: Added `faiss-cpu`.
- `src/utils/rag_utils.py`: New file containing RAG logic (loading, splitting, indexing, retrieval).
- `src/graph/state.py`: Added `rag_context` to `FinancialAgentState`.
- `src/graph/supervisor.py`: Added vector store initialization and retrieval logic.
- `src/agents/prompts.py`: Modified `finance_agent_system_prompt` to accept and include `rag_context`.
- `src/agents/account_agent.py`, `src/agents/transaction_agent.py`, `src/agents/card_agent.py`, `src/agents/exchange_rate_agent.py`: Changed agent creation to use dynamic `ChatPromptTemplate`s that pass `rag_context` to the prompt function.
