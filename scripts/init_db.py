import sqlite3
import os


def init_database(db_path: str = "edu_agent.db") -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS student_profiles (
        user_id TEXT PRIMARY KEY,
        profile_json TEXT NOT NULL,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT,
        messages TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS agent_logs (
        log_id TEXT PRIMARY KEY,
        session_id TEXT,
        agent_name TEXT,
        action TEXT,
        state TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        result TEXT
    );
    """)

    conn.commit()
    conn.close()
    print(f"数据库初始化完成 ✅  ({os.path.abspath(db_path)})")


if __name__ == "__main__":
    init_database()
