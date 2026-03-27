import sqlite3

conn = sqlite3.connect("events.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        title TEXT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        tags TEXT,
        campus TEXT DEFAULT 'Main',
        description TEXT DEFAULT ''
    )
    """
)


def _ensure_events_schema() -> None:
    cursor.execute("PRAGMA table_info(events)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    if "campus" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN campus TEXT DEFAULT 'Main'")

    if "description" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN description TEXT DEFAULT ''")

    conn.commit()

conn.commit()
_ensure_events_schema()


def seed_events():
    print("Seed_events is working")
    events = [
        ("1", "PRAXIS", "2026-03-28", "08:00", "18:00", "tech", "EC", "Annual innovation showcase"),
        ("2", "Integral Bee", "2026-04-11", "09:00", "13:00", "competition", "EC", "Mathematics problem solving contest"),
        ("3", "Hackfinity", "2026-03-29", "14:00", "17:00", "tech", "RR", "Collaborative coding sprint"),
        ("4", "Digital Twin & XR Hackathon", "2026-04-11", "09:00", "17:00", "tech", "EC", "Extended reality hackathon"),
        ("5", "Drama Night", "2026-04-01", "18:00", "21:00", "cultural", "RR", "Campus theatre performance")
    ]

    cursor.execute("DELETE FROM events")

    cursor.executemany(
        "INSERT INTO events (id, title, date, start_time, end_time, tags, campus, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        events
    )

    conn.commit()