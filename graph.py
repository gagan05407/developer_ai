from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from state import GraphState
from router import router_agent
from agents import general_agent, documentation_agent, debug_agent
from retriever import retrieve_documents, evaluate_self_rag, grade_crag_documents, web_search_fallback
import mcp_server
import memory

# Router Node
def router_node(state: GraphState) -> Dict[str, Any]:
    """Router Node: Classifies question route and loads persistent LTM profile facts."""
    trace = state.get("reasoning_trace", [])
    user_facts = memory.load_user_facts()
    route = router_agent(state["question"])
    trace.append(f"[Router Agent] Classified question into route: '{route.upper()}'.")
    if user_facts:
        trace.append(f"[LTM Database] Loaded {len(user_facts)} persistent user profile fact(s).")
    return {"route": route, "user_facts": user_facts, "reasoning_trace": trace}

# General Node
def general_node(state: GraphState) -> Dict[str, Any]:
    """General Node: Handles general programming with multi-turn memory & LTM facts."""
    trace = state.get("reasoning_trace", [])
    history = state.get("messages", [])
    user_facts = state.get("user_facts", {})
    trace.append("[General Agent] Invoked Gemini LLM with conversation history and persistent LTM facts.")
    answer = general_agent(state["question"], history=history, user_facts=user_facts)
    
    # Save assistant answer turn to SQLite LTM
    memory.save_chat_message("default_session", "assistant", answer, agent="general")
    
    return {
        "answer": answer,
        "route": "general",
        "tool_used": "None",
        "retrieved_docs": [],
        "citations": [],
        "reasoning_trace": trace
    }

# Docs Node (Integrated RAG + Self-RAG + CRAG + Web Search + Citations + LTM)
def docs_node(state: GraphState) -> Dict[str, Any]:
    """
    Docs Node: Integrates RAG, Self-RAG evaluation, CRAG grading, Web Search Fallback, Citations & LTM facts.
    """
    trace = state.get("reasoning_trace", [])
    history = state.get("messages", [])
    user_facts = state.get("user_facts", {})
    query = state["question"]
    
    # 1. Standard RAG Retrieval
    docs, citations = retrieve_documents(query, k=3)
    trace.append(f"[Retriever] Queried ChromaDB vector database -> Fetched {len(docs)} chunk(s).")
    
    # 2. Self-RAG (SRAG) Evaluation
    is_sufficient = evaluate_self_rag(query, docs)
    if not is_sufficient:
        trace.append("[Self-RAG Evaluator] Context graded as INSUFFICIENT -> Triggering re-retrieval loop (k=5).")
        docs, citations = retrieve_documents(query, k=5)
    else:
        trace.append("[Self-RAG Evaluator] Context graded as SUFFICIENT.")
        
    # 3. Corrective RAG (CRAG) Grading & Web Search Fallback
    is_relevant = grade_crag_documents(query, docs)
    if not is_relevant or not docs:
        trace.append("[CRAG Evaluator] Document context graded as IRRELEVANT -> Triggering Web Search Fallback.")
        docs, citations = web_search_fallback(query)
        tool_label = "CRAG: Live Web Search"
        trace.append("[CRAG Web Search] Successfully retrieved live web search results.")
    else:
        trace.append("[CRAG Evaluator] Document context graded as RELEVANT.")
        tool_label = "RAG / Self-RAG / CRAG"

    context_str = "\n\n".join(docs)
    trace.append("[Documentation Agent] Generating response with inline citations & LTM profile facts.")
    answer = documentation_agent(query, context=context_str, history=history, user_facts=user_facts)
    
    # Save assistant answer turn to SQLite LTM
    memory.save_chat_message("default_session", "assistant", answer, agent="docs")
    
    return {
        "answer": answer,
        "route": "docs",
        "tool_used": tool_label,
        "retrieved_docs": docs,
        "citations": citations,
        "reasoning_trace": trace
    }

# Debug Node (Tool Calling + MCP Server Integration + LTM)
def debug_node(state: GraphState) -> Dict[str, Any]:
    """
    Debug Node: Integrates tool calling, MCP server inspection, reasoning traces & LTM facts.
    """
    trace = state.get("reasoning_trace", [])
    history = state.get("messages", [])
    user_facts = state.get("user_facts", {})
    query = state["question"]
    tool_out = state.get("tool_used", "")

    # Check if user query targets local file reading via MCP
    if "readme" in query.lower() or "log" in query.lower() or "file" in query.lower():
        if "readme" in query.lower():
            tool_out = mcp_server.read_mcp_readme()
            tool_name = "MCP: read_mcp_readme"
        elif "log" in query.lower():
            tool_out = mcp_server.read_mcp_logs()
            tool_name = "MCP: read_mcp_logs"
        else:
            tool_out = mcp_server.list_mcp_dir(".")
            tool_name = "MCP: list_mcp_dir"
        trace.append(f"[MCP Server] Executed MCP file operation: '{tool_name}'.")
        answer = debug_agent(query, tool_output=tool_out, history=history, user_facts=user_facts)
    else:
        trace.append("[Debug Agent] Analyzing code error & checking tool bindings.")
        answer, tool_name = debug_agent(query, tool_output=tool_out, history=history, user_facts=user_facts)
        trace.append(f"[Tool Execution] Tool invoked: '{tool_name}'.")

    # Save assistant answer turn to SQLite LTM
    memory.save_chat_message("default_session", "assistant", answer, agent="debug")
        
    return {
        "answer": answer,
        "route": "debug",
        "tool_used": tool_name,
        "retrieved_docs": [],
        "citations": [],
        "reasoning_trace": trace
    }

# Conditional Routing Logic
def route_decision(state: GraphState) -> str:
    return state.get("route", "general")

# Workflow Construction
workflow = StateGraph(GraphState)

workflow.add_node("router", router_node)
workflow.add_node("general", general_node)
workflow.add_node("docs", docs_node)
workflow.add_node("debug", debug_node)

workflow.add_edge(START, "router")

workflow.add_conditional_edges(
    "router",
    route_decision,
    {
        "general": "general",
        "docs": "docs",
        "debug": "debug",
    }
)

workflow.add_edge("general", END)
workflow.add_edge("docs", END)
workflow.add_edge("debug", END)

# Compile Executable Graph
graph = workflow.compile()