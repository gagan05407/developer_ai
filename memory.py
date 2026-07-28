import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import config

DB_PATH = config.BASE_DIR / "developer_ai_ltm.db"

def init_db():
    """Initializes SQLite database tables for persistent LTM."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Chat History Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # User Profile Facts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT UNIQUE NOT NULL,
                fact_value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Ensure database tables exist on module import
init_db()

def save_chat_message(session_id: str, role: str, content: str, agent: str = "general"):
    """Saves a message turn permanently into SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chat_history (session_id, role, content, agent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, content, agent, datetime.datetime.now().isoformat()))
        conn.commit()

def load_chat_history(session_id: str = "default_session") -> List[Dict[str, Any]]:
    """Loads chat history from SQLite for a session."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, agent FROM chat_history
            WHERE session_id = ? ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1], "agent": r[2]} for r in rows]

def save_user_fact(key: str, value: str):
    """Saves or updates a permanent user profile fact in LTM."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profile_facts (fact_key, fact_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(fact_key) DO UPDATE SET
                fact_value = excluded.fact_value,
                updated_at = excluded.updated_at
        """, (key, value, datetime.datetime.now().isoformat()))
        conn.commit()

def load_user_facts() -> Dict[str, str]:
    """Loads all saved user profile facts from LTM."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT fact_key, fact_value FROM user_profile_facts")
        rows = cursor.fetchall()
        return {r[0]: r[1] for r in rows}

def clear_chat_history(session_id: str = "default_session"):
    """Deletes persistent chat history for a session."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
        conn.commit()

def clear_all_ltm():
    """Clears all persistent chat history and user facts from LTM."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history")
        cursor.execute("DELETE FROM user_profile_facts")
        conn.commit()
