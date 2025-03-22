import sqlite3
import time

class EventLogger:
    def __init__(self):
        self.conn = sqlite3.connect("ipc_events.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                timestamp REAL,
                process TEXT,
                event TEXT
            )
        """)
        self.conn.commit()

    def log(self, process, event):
        timestamp = time.time()
        self.cursor.execute("INSERT INTO events (timestamp, process, event) VALUES (?, ?, ?)",
                          (timestamp, process, event))
        self.conn.commit()

    def get_logs(self):
        self.cursor.execute("SELECT * FROM events")
        return self.cursor.fetchall()