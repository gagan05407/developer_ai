import warnings
warnings.filterwarnings("ignore")

import os
from pathlib import Path
from typing import List

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config
from embeddings import get_embeddings

_vectorstore_instance = None

def get_vectorstore() -> Chroma:
    """
    Returns persistent Chroma vectorstore instance.
    """
    global _vectorstore_instance
    if _vectorstore_instance is None:
        embeddings = get_embeddings()
        _vectorstore_instance = Chroma(
            collection_name="developer_ai_docs",
            embedding_function=embeddings,
            persist_directory=str(config.CHROMA_DB_DIR)
        )
    return _vectorstore_instance

def ingest_pdf(pdf_file_path: str) -> int:
    """
    Loads PDF, splits into chunks, and stores inside ChromaDB.
    Returns the count of ingested chunks.
    """
    path = Path(pdf_file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_file_path}")

    # Load PDF
    loader = PyPDFLoader(str(path))
    documents = loader.load()

    if not documents:
        return 0

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_documents(documents)

    # Store in ChromaDB
    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)

    return len(chunks)
