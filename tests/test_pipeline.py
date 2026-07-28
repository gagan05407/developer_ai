import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest
from router import router_agent
from tools import calculator, get_current_time, web_search_tool
from agents import _format_history
from graph import graph
import mcp_server
import memory

def test_ltm_memory_database():
    """Test SQLite persistent LTM database operations."""
    memory.init_db()
    memory.save_user_fact("user_name", "TestUser")
    facts = memory.load_user_facts()
    assert facts.get("user_name") == "TestUser"
    
    memory.save_chat_message("test_session", "user", "Hello LTM", agent="user")
    history = memory.load_chat_history("test_session")
    assert len(history) > 0
    assert history[0]["content"] == "Hello LTM"

def test_router_agent():
    """Test Router Agent classification accuracy."""
    assert router_agent("What is Python list?") == "general"
    assert router_agent("What is LangGraph?") == "docs"
    assert router_agent("Debug this code: for i in range(5) print(i)") == "debug"

def test_tools():
    """Test Calculator, Time, and Web Search tools."""
    calc_res = calculator.invoke({"expression": "10 * 5"})
    assert "50" in calc_res
    
    time_res = get_current_time.invoke({})
    assert "Current Time:" in time_res
    
    web_res = web_search_tool.invoke({"query": "Python release notes"})
    assert len(web_res) > 0

def test_mcp_server():
    """Test Python MCP server file reading tools."""
    readme_text = mcp_server.read_mcp_readme()
    assert "Developer AI Assistant" in readme_text

def test_memory_formatting():
    """Test multi-turn conversation memory history formatting."""
    messages = [
        {"role": "user", "content": "My name is Alex"},
        {"role": "assistant", "content": "Hello Alex!"}
    ]
    formatted = _format_history(messages)
    assert "User: My name is Alex" in formatted
    assert "Assistant: Hello Alex!" in formatted

def test_full_graph_execution():
    """Test full LangGraph execution with reasoning trace logging and LTM."""
    res = graph.invoke({
        "question": "What is a Python dictionary?",
        "messages": [],
        "user_facts": {},
        "route": "",
        "retrieved_docs": [],
        "tool_used": "",
        "reasoning_trace": [],
        "citations": [],
        "answer": ""
    })
    assert res["route"] == "general"
    assert len(res["answer"]) > 0
    assert len(res["reasoning_trace"]) > 0
    assert "[Router Agent]" in res["reasoning_trace"][0]
