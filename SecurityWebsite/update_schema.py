import sqlite3
conn = sqlite3.connect("alerts.db")
cur = conn.cursor()
cur.execute("SELECT id, image FROM alerts ORDER BY id DESC LIMIT 3")
print(cur.fetchall())
conn.close()