import re
from database import cur, conn

def normalize(title):
    return " ".join(re.sub(r"[^a-z0-9 ]", "", title.lower()).split()[:6])

def save_topic(title, source, date):
    cur.execute(
        "INSERT INTO topics VALUES (?,?,?)",
        (normalize(title), source, date)
    )
    conn.commit()

def daily_trends(date):
    cur.execute("""
        SELECT topic, COUNT(DISTINCT source)
        FROM topics
        WHERE date=?
        GROUP BY topic
        HAVING COUNT(DISTINCT source)>=2
    """, (date,))
    return cur.fetchall()
