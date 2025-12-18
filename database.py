import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS sent_news (
    link TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS topics (
    topic TEXT,
    source TEXT,
    date TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
""")
conn.commit()

def is_sent(link):
    cur.execute("SELECT 1 FROM sent_news WHERE link=?", (link,))
    return cur.fetchone() is not None

def mark_sent(link):
    cur.execute("INSERT OR IGNORE INTO sent_news VALUES (?)", (link,))
    conn.commit()

def get_setting(key, default=None):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone()
    return r[0] if r else default

def set_setting(key, value):
    cur.execute("REPLACE INTO settings VALUES (?,?)", (key, value))
    conn.commit()
