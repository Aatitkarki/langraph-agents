import os
import logging
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader # Using TextLoader for simplicity, can adapt later
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
    raise ValueError("OPENAI_API_KEY environment variable not set.")
EMBEDDING_MODEL = OpenAIEmbeddings()
TEXT_SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# --- Sample Data (Replace with actual data source loading) ---
# For demonstration, we'll use simple text strings.
# In a real scenario, load from files (CSV, TXT, PDF), databases, APIs etc.
# Example: loader = CSVLoader(file_path='./my_data.csv')
#          docs = loader.load()

sample_texts = [
    """
    **How do I check my account balance?**
    You can check your account balance using the 'get_account_summary' tool.
    Provide your account ID when prompted. The summary includes the current balance and account type.
    """,
    """
    **What are the transaction types?**
    Common transaction types include 'DEBIT', 'CREDIT', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE', and 'INTEREST'.
    You can view your recent transactions using the 'get_transaction_history' tool.
    """,
    """
    **How can I find my credit card limit?**
    Use the 'get_card_details' tool with your credit card ID.
    The details provided will include your credit limit, current balance, and payment due date.
    """,
    """
    **What is the process for currency exchange?**
    To get current exchange rates or perform a conversion, use the 'get_exchange_rate' or 'convert_currency' tools.
    Specify the source currency, target currency, and amount (for conversion).
    """,
    """
    **Security Best Practices:**
    Never share your account password or PIN. Be cautious of phishing emails asking for sensitive information.
    Monitor your account regularly for unauthorized transactions. Report suspicious activity immediately.
    """
]

# Convert sample texts to LangChain Document objects
sample_docs = [Document(page_content=text, metadata={"source": "internal_faq"}) for text in sample_texts]
# -------------------------------------------------------------

def setup_vector_store():
    """Initializes the PGVector store and ensures the collection exists."""
    logger.info(f"Initializing vector store. Connection: {DB_CONNECTION_STRING.split('@')[-1]}, Collection: {COLLECTION_NAME}") # Avoid logging password
    try:
        store = PGVector(
            connection_string=DB_CONNECTION_STRING,
            embedding_function=EMBEDDING_MODEL,
            collection_name=COLLECTION_NAME,
            # distance_strategy=DistanceStrategy.COSINE, # Default is COSINE
            pre_delete_collection=False # Set to True to clear collection before adding new docs
        )
        logger.info("Vector store initialized successfully.")
        return store
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
        # Provide more specific guidance based on common errors
        if "database" in str(e) and "does not exist" in str(e):
             logger.error(f"Database '{os.environ.get('POSTGRES_DB')}' not found. Please ensure it exists.")
        elif "connection refused" in str(e):
             logger.error(f"Connection refused. Is the PostgreSQL server running at {os.environ.get('POSTGRES_HOST')}:{os.environ.get('POSTGRES_PORT')} and accepting connections?")
        elif "authentication failed" in str(e):
             logger.error(f"Database authentication failed for user '{os.environ.get('POSTGRES_USER')}'. Check credentials.")
        elif "vector extension not installed" in str(e) or "type \"vector\" does not exist" in str(e):
             logger.error("The 'vector' extension is not installed or enabled in your PostgreSQL database. Run 'CREATE EXTENSION IF NOT EXISTS vector;'")
        raise

def load_data_to_vector_store(store: PGVector, documents: list[Document]):
    """Splits documents, generates embeddings, and adds them to the vector store."""
    if not documents:
        logger.warning("No documents provided to load.")
        return

    logger.info(f"Splitting {len(documents)} documents...")
    split_docs = TEXT_SPLITTER.split_documents(documents)
    logger.info(f"Split into {len(split_docs)} chunks.")

    if not split_docs:
        logger.warning("No chunks generated after splitting.")
        return

    logger.info(f"Adding {len(split_docs)} document chunks to collection '{COLLECTION_NAME}'...")
    try:
        store.add_documents(split_docs, ids=None) # Let PGVector handle IDs or provide your own
        logger.info("Successfully added documents to the vector store.")
    except Exception as e:
        logger.error(f"Failed to add documents to vector store: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("--- Starting Vector Data Loading Script ---")
    try:
        vector_store = setup_vector_store()
        # In a real application, load documents from your actual data source here
        logger.info("Loading sample FAQ data...")
        load_data_to_vector_store(vector_store, sample_docs)
        logger.info("--- Vector Data Loading Script Finished ---")
    except Exception as e:
        logger.error(f"An error occurred during the data loading process: {e}", exc_info=True)
        logger.info("--- Vector Data Loading Script Failed ---")