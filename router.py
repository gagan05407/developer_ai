import re
from config import get_llm
from prompts import ROUTER_PROMPT

def _extract_text(content) -> str:
    """Safely extract text string from LLM response (handles str or list of content blocks)."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            elif hasattr(part, "text"):
                parts.append(part.text)
        return " ".join(parts)
    return str(content)

def router_agent(question: str) -> str:
    """
    Router Agent: Classifies the incoming question into 'general', 'docs', or 'debug'.
    """
    llm = get_llm()
    prompt = ROUTER_PROMPT.format(question=question)
    
    try:
        response = llm.invoke(prompt)
        raw_text = _extract_text(response.content).strip().lower()
        matches = re.findall(r"\b(general|docs|debug)\b", raw_text)
        route = matches[-1] if matches else "general"
        return route
    except Exception as e:
        print(f"[Router Warning] Routing failed: {e}. Defaulting to 'general'.")
        return "general"
