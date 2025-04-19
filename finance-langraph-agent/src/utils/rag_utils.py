# src/utils/rag_utils.py
import os
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- Configuration ---
# Consider moving these to a config file or environment variables
PDF_SOURCE_DIR = "knowledge_base"  # Directory containing PDF files
VECTOR_STORE_PATH = "vector_store/faiss_index"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Ensure base directories exist
os.makedirs(PDF_SOURCE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(VECTOR_STORE_PATH), exist_ok=True)

# --- Core RAG Functions ---

def load_pdfs(source_dir: str = PDF_SOURCE_DIR) -> List[Document]:
    """Loads all PDF files from the specified directory."""
    docs = []
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(source_dir, filename)
            try:
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return docs

def split_documents(docs: List[Document]) -> List[Document]:
    """Splits documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(docs)

def create_or_load_vector_store(
    docs: Optional[List[Document]] = None,
    vector_store_path: str = VECTOR_STORE_PATH,
    force_recreate: bool = False
) -> FAISS:
    """
    Creates a new FAISS vector store from documents or loads an existing one.

    Args:
        docs: List of documents to index. Required if creating a new store
              or if force_recreate is True.
        vector_store_path: Path to save/load the FAISS index.
        force_recreate: If True, always create a new index even if one exists.

    Returns:
        A FAISS vector store instance.
    """
    embeddings = OpenAIEmbeddings() # Assumes OPENAI_API_KEY is set in env

    if not force_recreate and os.path.exists(vector_store_path):
        print(f"Loading existing vector store from {vector_store_path}")
        try:
            vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
            print("Vector store loaded successfully.")
            # If new docs are provided, add them to the existing store
            if docs:
                 print(f"Adding {len(docs)} new documents to the existing store...")
                 vector_store.add_documents(docs)
                 print("New documents added. Saving updated store...")
                 vector_store.save_local(vector_store_path)
                 print("Updated vector store saved.")
            return vector_store
        except Exception as e:
            print(f"Error loading existing vector store: {e}. Will attempt to recreate.")
            # Fall through to recreate if loading fails

    if not docs:
        raise ValueError("Documents must be provided to create a new vector store.")

    print(f"Creating new vector store with {len(docs)} documents...")
    vector_store = FAISS.from_documents(docs, embeddings)
    print("Vector store created. Saving...")
    vector_store.save_local(vector_store_path)
    print(f"Vector store saved to {vector_store_path}")
    return vector_store

def build_rag_pipeline(force_recreate: bool = False):
    """Loads PDFs, splits them, and builds/loads the vector store."""
    print("Starting RAG pipeline build...")
    # 1. Load documents only if we need to create/update the store
    docs_to_index = None
    if force_recreate or not os.path.exists(VECTOR_STORE_PATH):
        print("Loading PDF documents...")
        raw_docs = load_pdfs()
        if not raw_docs:
            print("No PDF documents found. Cannot build vector store.")
            # Try loading existing store if it exists, otherwise raise error
            if os.path.exists(VECTOR_STORE_PATH):
                 print("Attempting to load existing vector store...")
                 return create_or_load_vector_store(vector_store_path=VECTOR_STORE_PATH)
            else:
                 raise FileNotFoundError(f"No PDFs found in {PDF_SOURCE_DIR} and no existing vector store at {VECTOR_STORE_PATH}")
        print(f"Loaded {len(raw_docs)} raw document pages.")
        print("Splitting documents...")
        docs_to_index = split_documents(raw_docs)
        print(f"Split into {len(docs_to_index)} chunks.")
    else:
        print("Vector store exists and force_recreate is False. Skipping document loading and splitting.")


    # 2. Create or load vector store
    vector_store = create_or_load_vector_store(
        docs=docs_to_index, # Will be None if not recreating/initially building
        vector_store_path=VECTOR_STORE_PATH,
        force_recreate=force_recreate
    )
    print("RAG pipeline build finished.")
    return vector_store

def retrieve_documents(query: str, vector_store: FAISS, k: int = 5) -> List[Document]:
    """Retrieves the top k relevant documents for a given query."""
    print(f"Retrieving top {k} documents for query: '{query}'")
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    results = retriever.invoke(query)
    print(f"Retrieved {len(results)} documents.")
    return results

# --- Example Usage (Optional - can be run directly) ---
if __name__ == "__main__":
    print("Running RAG utility script directly...")

    # Create a dummy PDF for testing if none exist
    dummy_pdf_path = os.path.join(PDF_SOURCE_DIR, "dummy_finance_guide.pdf")
    if not os.path.exists(dummy_pdf_path) and not any(f.lower().endswith(".pdf") for f in os.listdir(PDF_SOURCE_DIR)):
         print("Creating a dummy PDF for testing...")
         try:
             from reportlab.pdfgen import canvas
             from reportlab.lib.pagesizes import letter
             c = canvas.Canvas(dummy_pdf_path, pagesize=letter)
             c.drawString(100, 750, "Dummy Financial Document")
             c.drawString(100, 735, "This document contains basic information about savings accounts.")
             c.drawString(100, 720, "Savings accounts are a safe place to store money.")
             c.save()
             print(f"Dummy PDF created at {dummy_pdf_path}")
         except ImportError:
             print("Could not import reportlab. Please install it (`pip install reportlab`) to create a dummy PDF.")
         except Exception as e:
             print(f"Error creating dummy PDF: {e}")


    # Build or load the vector store (force recreate for demonstration if needed)
    vs = build_rag_pipeline(force_recreate=False) # Set to True to rebuild index

    # Example retrieval
    if vs:
        test_query = "What are savings accounts?"
        retrieved_docs = retrieve_documents(test_query, vs)
        print("\n--- Retrieval Results ---")
        for i, doc in enumerate(retrieved_docs):
            print(f"\n--- Document {i+1} ---")
            print(f"Source: {doc.metadata.get('source', 'N/A')}")
            # print(f"Content: {doc.page_content[:200]}...") # Print snippet
            print(f"Content: {doc.page_content}")
    else:
        print("Vector store could not be built or loaded.")

    print("\nRAG utility script finished.")