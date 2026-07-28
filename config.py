import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Ensure target directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# API Key Validation
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    # Fallback / Warning if key is missing
    print("[WARNING] GOOGLE_API_KEY environment variable is not set.")

# Central LLM Model Name
DEFAULT_MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Singleton LLM Instance Manager
_llm_instance = None

def get_llm(model_name: str = DEFAULT_MODEL, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """
    Returns a shared, reusable ChatGoogleGenerativeAI instance.
    Prevents duplicate initialization of the LLM across modules.
    """
    global _llm_instance
    if _llm_instance is None:
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY missing from environment. Please add it to your .env file.")
        _llm_instance = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GOOGLE_API_KEY,
            temperature=temperature,
        )
    return _llm_instance
