import sys
import io
import math
import datetime
from pathlib import Path
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize Web Search Tool
_search = DuckDuckGoSearchRun()

@tool
def web_search_tool(query: str) -> str:
    """
    Performs live web search for out-of-domain knowledge, recent framework docs, or external questions.
    """
    try:
        results = _search.run(query)
        return results if results else "No relevant web search results found."
    except Exception as e:
        return f"Web Search Error: {e}"

@tool
def calculator(expression: str) -> str:
    """
    Evaluates mathematical expressions safely.
    Example input: '2 + 2 * 10' or 'math.sqrt(16)'
    """
    try:
        allowed_names = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "sum": sum,
        }
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculator Error: {e}"

@tool
def get_current_time(query: str = "") -> str:
    """
    Returns the current local date and time.
    """
    now = datetime.datetime.now()
    return f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"

@tool
def read_local_file(file_path: str) -> str:
    """
    Reads and returns the contents of a local file path.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        content = path.read_text(encoding="utf-8")
        return content[:4000]
    except Exception as e:
        return f"File Read Error: {e}"

@tool
def execute_python_code(code_string: str) -> str:
    """
    Executes Python code and captures stdout or runtime exception tracebacks.
    """
    buffer = io.StringIO()
    sys_stdout = sys.stdout
    try:
        sys.stdout = buffer
        exec_globals = {"__builtins__": __builtins__}
        exec(code_string, exec_globals)
        sys.stdout = sys_stdout
        output = buffer.getvalue().strip()
        return output if output else "Execution successful with no output."
    except Exception as e:
        sys.stdout = sys_stdout
        return f"Execution Error ({type(e).__name__}): {e}"

ALL_TOOLS = [web_search_tool, calculator, get_current_time, read_local_file, execute_python_code]
TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}
