import sqlite3

conn = sqlite3.connect("events.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    tags TEXT
)
""")

conn.commit()


def seed_events():
    print("Seed_events is working")
    events = [
        ("1", "PRAXIS", "2026-03-28", "08:00", "18:00", "tech","EC"),
        ("2", "Integral Bee", "2026-04-11", "09:00", "13:00", "competition","EC"),
        ("3", "Hackfinity", "2026-03-29", "14:00", "17:00", "tech","RR"),
        ("4", "Digital Twin & XR Hackathon", "2026-04-11", "09:00", "17:00", "tech", "EC"),
        ("5", "Drama Night", "2026-04-01", "18:00", "21:00", "cultural")
    ]

    cursor.execute("DELETE FROM events")

    cursor.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        events
    )

    conn.commit()