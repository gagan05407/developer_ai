import warnings
warnings.filterwarnings("ignore")

from langchain_community.embeddings import HuggingFaceEmbeddings
import config

_embedding_instance = None

def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns a singleton instance of HuggingFaceEmbeddings using SentenceTransformers.
    """
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME
        )
    return _embedding_instance
