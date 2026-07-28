from typing import List, Dict, Tuple
from vectorstore import get_vectorstore
from config import get_llm
from prompts import SELF_RAG_EVAL_PROMPT, CRAG_GRADE_PROMPT
from tools import web_search_tool

def retrieve_documents(query: str, k: int = 3) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Standard RAG Retriever: Queries ChromaDB for top k relevant document chunks.
    Returns tuple of (formatted_docs_with_citations, citations_list).
    """
    try:
        vectorstore = get_vectorstore()
        results = vectorstore.similarity_search(query, k=k)
        docs = []
        citations = []
        for idx, doc in enumerate(results, 1):
            source = doc.metadata.get("source", f"ChromaDB Chunk {idx}")
            doc_label = f"[Doc {idx}]"
            docs.append(f"{doc_label} ({source}):\n{doc.page_content}")
            citations.append({"label": doc_label, "source": source, "content": doc.page_content[:200]})
        return docs, citations
    except Exception as e:
        print(f"[Retriever Warning] Similarity search failed: {e}")
        return [], []

def web_search_fallback(query: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Web Search Fallback for CRAG: Queries live web search when document context fails.
    """
    try:
        raw_result = web_search_tool.invoke({"query": query})
        doc_label = "[Web Search 1]"
        docs = [f"{doc_label} (DuckDuckGo Live Search):\n{raw_result}"]
        citations = [{"label": doc_label, "source": "DuckDuckGo Live Web Search", "content": raw_result[:200]}]
        return docs, citations
    except Exception as e:
        print(f"[Web Search Fallback Warning] {e}")
        return [], []

def evaluate_self_rag(query: str, context_chunks: List[str]) -> bool:
    """
    Self-RAG Evaluator: Evaluates if retrieved context is sufficient for answering the query.
    Returns True if 'YES', False if 'NO'.
    """
    if not context_chunks:
        return False
        
    llm = get_llm()
    context_str = "\n\n".join(context_chunks)
    prompt = SELF_RAG_EVAL_PROMPT.format(context=context_str, question=query)
    
    try:
        response = llm.invoke(prompt)
        text = str(response.content).strip().upper()
        return "YES" in text
    except Exception:
        return True

def grade_crag_documents(query: str, context_chunks: List[str]) -> bool:
    """
    Corrective-RAG (CRAG) Evaluator: Grades context relevance.
    Returns True if 'RELEVANT', False if 'IRRELEVANT'.
    """
    if not context_chunks:
        return False
        
    llm = get_llm()
    context_str = "\n\n".join(context_chunks)
    prompt = CRAG_GRADE_PROMPT.format(context=context_str, question=query)
    
    try:
        response = llm.invoke(prompt)
        text = str(response.content).strip().upper()
        return "RELEVANT" in text
    except Exception:
        return True
