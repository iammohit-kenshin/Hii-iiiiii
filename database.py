import sqlite3

conn = sqlite3.connect("cache.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    link TEXT PRIMARY KEY,
    file_id TEXT
)
""")
conn.commit()

def get_cached(link):
    cursor.execute("SELECT file_id FROM videos WHERE link=?", (link,))
    result = cursor.fetchone()
    return result[0] if result else None

def save_cache(link, file_id):
    cursor.execute("INSERT OR REPLACE INTO videos VALUES (?,?)", (link, file_id))
    conn.commit()
