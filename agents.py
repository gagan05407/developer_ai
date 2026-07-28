import re
from typing import List, Dict, Any, Tuple
from config import get_llm
from prompts import (
    GENERAL_AGENT_PROMPT,
    DOCUMENTATION_AGENT_PROMPT,
    DEBUG_AGENT_PROMPT
)
from tools import ALL_TOOLS, execute_python_code, calculator, get_current_time, read_local_file, web_search_tool
import memory

def _extract_text(content) -> str:
    """Safely extract text string from LLM response."""
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

def _format_history(messages: List[Dict[str, Any]]) -> str:
    """Formats conversation history into structured prompt text."""
    if not messages:
        return "No prior conversation history."
    formatted = []
    for msg in messages[-6:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        formatted.append(f"{role}: {content}")
    return "\n".join(formatted)

def _format_user_facts(user_facts: Dict[str, str]) -> str:
    """Formats saved persistent user profile facts into prompt text."""
    if not user_facts:
        return "No persistent user profile facts saved yet."
    return "\n".join([f"- {k}: {v}" for k, v in user_facts.items()])

def extract_and_save_user_facts(question: str):
    """
    Regex/heuristic rule to auto-detect and persist key user facts into SQLite LTM.
    """
    # Name extraction (e.g. "My name is Alex", "I am Alex")
    name_match = re.search(r"\b(?:my name is|i am|call me)\s+([A-Z][a-z]+)\b", question, re.IGNORECASE)
    if name_match:
        memory.save_user_fact("user_name", name_match.group(1).capitalize())

    # Preferred language extraction (e.g. "I prefer Python", "My favorite language is Rust")
    lang_match = re.search(r"\b(?:prefer|favorite language is)\s+(Python|JavaScript|TypeScript|C\+\+|Java|Rust|Go)\b", question, re.IGNORECASE)
    if lang_match:
        memory.save_user_fact("preferred_language", lang_match.group(1).capitalize())

def general_agent(question: str, history: List[Dict[str, Any]] = None, user_facts: Dict[str, str] = None) -> str:
    """General Agent: Handles Python concepts, DSA, and general software questions with conversation memory and LTM profile facts."""
    extract_and_save_user_facts(question)
    facts_map = user_facts if user_facts is not None else memory.load_user_facts()
    llm = get_llm()
    hist_str = _format_history(history or [])
    facts_str = _format_user_facts(facts_map)
    prompt = GENERAL_AGENT_PROMPT.format(user_facts=facts_str, history=hist_str, question=question)
    response = llm.invoke(prompt)
    return _extract_text(response.content)

def documentation_agent(question: str, context: str = "", history: List[Dict[str, Any]] = None, user_facts: Dict[str, str] = None) -> str:
    """Documentation Agent: Answers framework and library questions with citations, history, and LTM profile facts."""
    extract_and_save_user_facts(question)
    facts_map = user_facts if user_facts is not None else memory.load_user_facts()
    llm = get_llm()
    context_str = context if context else "No extra document context provided."
    hist_str = _format_history(history or [])
    facts_str = _format_user_facts(facts_map)
    prompt = DOCUMENTATION_AGENT_PROMPT.format(user_facts=facts_str, context=context_str, history=hist_str, question=question)
    response = llm.invoke(prompt)
    return _extract_text(response.content)

def debug_agent(question: str, tool_output: str = "", history: List[Dict[str, Any]] = None, user_facts: Dict[str, str] = None) -> Tuple[str, str]:
    """
    Debug Agent: Debugs code and executes tools when needed.
    Returns tuple of (answer, tool_name_executed).
    """
    extract_and_save_user_facts(question)
    facts_map = user_facts if user_facts is not None else memory.load_user_facts()
    tool_executed_name = "None"
    tool_out_str = tool_output

    lower_q = question.lower()
    if "time" in lower_q or "date" in lower_q:
        tool_out_str = get_current_time.invoke({})
        tool_executed_name = "get_current_time"
    elif "calculate" in lower_q or "math" in lower_q or "sqrt" in lower_q or "+" in lower_q or "*" in lower_q:
        expr_match = re.search(r"([\d\.\s\+\-\*\/\(\)]+)", question)
        if expr_match and len(expr_match.group(1).strip()) > 2:
            tool_out_str = calculator.invoke({"expression": expr_match.group(1).strip()})
            tool_executed_name = "calculator"

    llm = get_llm()
    try:
        llm_with_tools = llm.bind_tools(ALL_TOOLS)
        response = llm_with_tools.invoke(question)
        if hasattr(response, "tool_calls") and response.tool_calls:
            first_call = response.tool_calls[0]
            t_name = first_call.get("name")
            t_args = first_call.get("args", {})
            for t in ALL_TOOLS:
                if t.name == t_name:
                    tool_out_str = t.invoke(t_args)
                    tool_executed_name = t_name
                    break
    except Exception:
        pass

    hist_str = _format_history(history or [])
    facts_str = _format_user_facts(facts_map)
    prompt = DEBUG_AGENT_PROMPT.format(user_facts=facts_str, tool_output=tool_out_str, history=hist_str, question=question)
    final_response = llm.invoke(prompt)
    answer = _extract_text(final_response.content)
    
    return answer, tool_executed_name