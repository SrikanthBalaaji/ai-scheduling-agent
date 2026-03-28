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
        description TEXT DEFAULT '',
        club_name TEXT DEFAULT '',
        location TEXT DEFAULT '',
        mode TEXT DEFAULT 'offline',
        event_type TEXT DEFAULT 'event',
        poster_url TEXT DEFAULT '',
        google_form_url TEXT DEFAULT ''
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

    if "club_name" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN club_name TEXT DEFAULT ''")

    if "location" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN location TEXT DEFAULT ''")

    if "mode" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN mode TEXT DEFAULT 'offline'")

    if "event_type" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN event_type TEXT DEFAULT 'event'")

    if "poster_url" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN poster_url TEXT DEFAULT ''")

    if "google_form_url" not in existing_columns:
        cursor.execute("ALTER TABLE events ADD COLUMN google_form_url TEXT DEFAULT ''")

    conn.commit()

conn.commit()
_ensure_events_schema()


def seed_events():
    print("Seed_events is working")
    cursor.execute("SELECT COUNT(*) FROM events")
    existing_count = cursor.fetchone()[0]
    if existing_count:
        return

    events = [
        ("1", "PRAXIS", "2026-03-30", "08:00", "18:00", "tech", "EC", "Annual innovation showcase", "", "EC Campus", "offline", "tech", "", ""),
        ("2", "Integral Bee", "2026-04-11", "09:00", "13:00", "competition", "EC", "Mathematics problem solving contest", "", "EC Campus", "offline", "competition", "", ""),
        ("3", "Hackfinity", "2026-03-29", "14:00", "17:00", "tech", "RR", "Collaborative coding sprint", "", "RR Campus", "offline", "tech", "", ""),
        ("4", "Digital Twin & XR Hackathon", "2026-04-11", "09:00", "17:00", "tech", "EC", "Extended reality hackathon", "", "EC Campus", "offline", "tech", "", ""),
        ("5", "Drama Night", "2026-04-01", "18:00", "21:00", "cultural", "RR", "Campus theatre performance", "", "RR Campus", "offline", "cultural", "", "")
    ]

    cursor.executemany(
        "INSERT INTO events (id, title, date, start_time, end_time, tags, campus, description, club_name, location, mode, event_type, poster_url, google_form_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        events
    )

    conn.commit()