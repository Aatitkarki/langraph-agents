import os
import logging
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
DB_CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver="psycopg2",
    host=os.environ.get("POSTGRES_HOST", "localhost"),
    port=int(os.environ.get("POSTGRES_PORT", 5432)),
    database=os.environ.get("POSTGRES_DB", "vectordb"),
    user=os.environ.get("POSTGRES_USER", "user"),
    password=os.environ.get("POSTGRES_PASSWORD", "password"),
)
COLLECTION_NAME = "financial_docs"
# Ensure OPENAI_API_KEY is set in your environment
if not os.environ.get("OPENAI_API_KEY"):
    # Log a warning instead of raising an error immediately,
    # as the tool might be imported before the key is needed for execution.
    logger.warning("OPENAI_API_KEY environment variable not set. Retrieval will fail if called.")
    EMBEDDING_MODEL = None # Set to None if key is missing
else:
    EMBEDDING_MODEL = OpenAIEmbeddings()

# --- Initialize Vector Store (as retriever) ---
# We initialize it here so the tool function can use it.
# This assumes the DB and extension are ready when the app runs.
try:
    if EMBEDDING_MODEL:
        vector_store = PGVector(
            connection_string=DB_CONNECTION_STRING,
            embeddings=EMBEDDING_MODEL, # Corrected parameter name
            collection_name=COLLECTION_NAME,
            # distance_strategy=DistanceStrategy.COSINE, # Default
        )
        retriever = vector_store.as_retriever(
            search_type="similarity", # Or "similarity_score_threshold", "mmr"
            search_kwargs={'k': 3} # Retrieve top 3 relevant chunks
        )
        logger.info("PGVector retriever initialized successfully.")
    else:
        retriever = None
        logger.warning("PGVector retriever could not be initialized due to missing OpenAI API key.")

except Exception as e:
    logger.error(f"Failed to initialize PGVector retriever: {e}", exc_info=True)
    retriever = None # Ensure retriever is None if initialization fails

# --- RAG Tool Definition ---
@tool
def search_financial_docs(query: str) -> str:
    """
    Searches the financial knowledge base (FAQs, documentation) for information relevant to the user's query.
    Use this tool when the user asks general questions about financial procedures, terms, or how to use specific features
    that might be answered by documentation, BEFORE attempting to use other specialized tools like checking balances or transactions.
    For example: 'How do I check my balance?', 'What are transaction types?', 'Tell me about security best practices.'
    Args:
        query (str): The user's query or question to search for in the knowledge base.
    Returns:
        str: A string containing the relevant information found, or a message indicating that no relevant information was found.
    """
    logger.info(f"Executing RAG search for query: '{query}'")
    if not retriever:
        logger.error("Retriever is not available (check initialization errors or API key).")
        return "Error: The financial knowledge base is currently unavailable."
    if not query:
        return "Error: No query provided for searching the knowledge base."

    try:
        results = retriever.invoke(query)
        if results:
            # Format results for the LLM
            context = "\n\n---\n\n".join([doc.page_content for doc in results])
            logger.info(f"Found {len(results)} relevant document chunks.")
            return f"Found relevant information in the knowledge base:\n\n{context}"
        else:
            logger.info("No relevant documents found in the knowledge base.")
            return "No specific information found in the knowledge base for that query."
    except Exception as e:
        logger.error(f"Error during RAG search: {e}", exc_info=True)
        return f"An error occurred while searching the knowledge base: {e}"

# Example usage (for testing purposes)
if __name__ == "__main__":
    test_query = "How to check balance"
    print(f"Testing RAG tool with query: '{test_query}'")
    # Ensure dependencies are installed and DB is running with vector extension enabled
    # and data loaded using load_vector_data.py before running this test.
    if retriever:
        search_result = search_financial_docs(test_query)
        print("\nSearch Result:")
        print(search_result)
    else:
        print("\nRetriever not initialized. Cannot run test.")