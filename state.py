from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    """
    Represents the complete state of the LangGraph execution graph.
    
    Attributes:
        question: Current user query.
        messages: List of past messages for multi-turn conversation memory.
        user_facts: Persistent user profile facts loaded from SQLite LTM.
        route: Active route label ('general', 'docs', 'debug').
        retrieved_docs: List of retrieved context documents with citation markers.
        tool_used: Name of executed tools or fallbacks.
        reasoning_trace: Step-by-step reasoning and decision log.
        citations: List of source citations (documents, web search, MCP).
        answer: Final generated response string.
    """
    question: str
    messages: List[Dict[str, Any]]
    user_facts: Dict[str, str]
    route: str
    retrieved_docs: List[str]
    tool_used: Optional[str]
    reasoning_trace: List[str]
    citations: List[Dict[str, str]]
    answer: str
