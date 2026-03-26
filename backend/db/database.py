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
        ("1", "Hackathon", "2026-03-30", "10:00", "18:00", "tech"),
        ("2", "Music Night", "2026-03-30", "17:00", "20:00", "cultural"),
        ("3", "AI Workshop", "2026-03-31", "14:00", "17:00", "tech"),
        ("4", "Football Match", "2026-03-31", "16:00", "18:00", "sports"),
        ("5", "Drama Night", "2026-04-01", "18:00", "21:00", "cultural")
    ]

    cursor.execute("DELETE FROM events")

    cursor.executemany(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
        events
    )

    conn.commit()