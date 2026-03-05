"""
database.py — SQLite-backed persistence for TagMaster Bot
All tables are auto-created on first run.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "tagmaster.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                first_name TEXT,
                username   TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS groups (
                chat_id    INTEGER PRIMARY KEY,
                title      TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS group_members (
                chat_id    INTEGER,
                user_id    INTEGER,
                first_name TEXT,
                PRIMARY KEY (chat_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS tag_states (
                chat_id  INTEGER,
                task_key TEXT,
                state    TEXT DEFAULT 'idle',
                PRIMARY KEY (chat_id, task_key)
            );
        """)


def save_user(user_id: int, first_name: str, username: str = None):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, first_name, username) VALUES (?, ?, ?)",
            (user_id, first_name, username),
        )


def save_group(chat_id: int, title: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO groups (chat_id, title) VALUES (?, ?)",
            (chat_id, title),
        )


def save_member(chat_id: int, user_id: int, first_name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO group_members (chat_id, user_id, first_name) VALUES (?, ?, ?)",
            (chat_id, user_id, first_name),
        )


def get_group_members(chat_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_id, first_name FROM group_members WHERE chat_id = ?",
            (chat_id,),
        ).fetchall()
    return [{"user_id": r["user_id"], "first_name": r["first_name"]} for r in rows]


def get_stats() -> dict:
    with get_conn() as conn:
        users  = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        groups = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
    return {"users": users, "groups": groups}


def get_all_users() -> list:
    with get_conn() as conn:
        return [r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]


def get_all_groups() -> list:
    with get_conn() as conn:
        return [r[0] for r in conn.execute("SELECT chat_id FROM groups").fetchall()]


def set_tag_state(chat_id: int, task_key: str, state: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO tag_states (chat_id, task_key, state) VALUES (?, ?, ?)",
            (chat_id, task_key, state),
        )


def get_tag_state(chat_id: int, task_key: str) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT state FROM tag_states WHERE chat_id = ? AND task_key = ?",
            (chat_id, task_key),
        ).fetchone()
    return row["state"] if row else "idle"


# Auto-init on import
init_db()
