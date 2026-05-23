import sqlite3, json
conn = sqlite3.connect("edu_agent.db")
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== Tables ===")
for t in tables:
    name = t[0]
    count = cursor.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  {name}: {count} rows")

# 查看student_profiles内容
print("\n=== student_profiles ===")
try:
    rows = cursor.execute("SELECT user_id, profile_json, update_time FROM student_profiles").fetchall()
    for r in rows:
        print(f"  user_id={r[0]}")
        print(f"  profile={r[1][:200]}")
        print(f"  update_time={r[2]}")
except Exception as e:
    print(f"  Error: {e}")

# 查看agent_logs最近5条
print("\n=== agent_logs (last 5) ===")
try:
    rows = cursor.execute("SELECT agent_name, action, timestamp FROM agent_logs ORDER BY timestamp DESC LIMIT 5").fetchall()
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]}")
except Exception as e:
    print(f"  Error: {e}")

# 查看chat_sessions
print("\n=== chat_sessions ===")
try:
    rows = cursor.execute("SELECT session_id, user_id FROM chat_sessions").fetchall()
    for r in rows:
        print(f"  session={r[0]} user={r[1]}")
except Exception as e:
    print(f"  Error: {e}")

conn.close()
