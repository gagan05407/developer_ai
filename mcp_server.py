"""
Python Model Context Protocol (MCP) Server.
Exposes file system tools and environment inspection to the LangGraph agents.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def list_mcp_dir(dir_path: str = ".") -> str:
    """
    MCP Tool: Lists files and subdirectories under the target directory path.
    """
    try:
        target = (BASE_DIR / dir_path).resolve()
        if not target.exists():
            return f"MCP Error: Directory '{dir_path}' does not exist."
        items = [f"{'[DIR]' if p.is_dir() else '[FILE]'} {p.name}" for p in target.iterdir()]
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"MCP Error listing directory: {e}"

def read_mcp_file(file_path: str) -> str:
    """
    MCP Tool: Reads contents of a file within the project repository.
    """
    try:
        target = (BASE_DIR / file_path).resolve()
        if not target.exists():
            return f"MCP Error: File '{file_path}' does not exist."
        return target.read_text(encoding="utf-8")[:4000]
    except Exception as e:
        return f"MCP Error reading file: {e}"

def read_mcp_readme() -> str:
    """
    MCP Tool: Reads the project README.md file.
    """
    readme_path = BASE_DIR / "README.md"
    if not readme_path.exists():
        return "README.md file does not exist yet."
    return readme_path.read_text(encoding="utf-8")

def read_mcp_logs() -> str:
    """
    MCP Tool: Reads project log files if present.
    """
    log_file = BASE_DIR / "app.log"
    if not log_file.exists():
        return "No active app.log file found."
    return log_file.read_text(encoding="utf-8")[-2000:]
