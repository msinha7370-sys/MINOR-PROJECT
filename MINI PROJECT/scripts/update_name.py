import sqlite3
import sys

db = 'tourism.db'
try:
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("UPDATE attractions SET name = ? WHERE name = ?", ('RED FORT','Heritage Fort'))
    updated = c.rowcount
    conn.commit()
    conn.close()
    print(f"Updated rows: {updated}")
except Exception as e:
    print('Error:', e)
    sys.exit(1)
