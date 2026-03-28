import sqlite3
import hashlib

conn = sqlite3.connect("events.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        interests TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
)

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


def _ensure_users_schema() -> None:
    """Ensure users table has all required columns"""
    try:
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "username" not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT UNIQUE")
            conn.commit()
            print("✅ Added username column to users table")
    except Exception as e:
        print(f"Schema migration error: {e}")


def _ensure_events_schema() -> None:
    """Ensure events table has all required columns"""
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
_ensure_users_schema()
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


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(user_id: str, username: str, name: str, password: str, role: str = "student", interests: str = ""):
    """Create a new user in the database"""
    try:
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (id, username, name, password, role, interests) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, name, hashed_password, role, interests)
        )
        conn.commit()
        return {"success": True, "message": "User created successfully"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists"}
    except Exception as e:
        return {"success": False, "message": str(e)}


def login_user(username: str, password: str):
    """Authenticate a user"""
    try:
        cursor.execute("SELECT id, name, role, interests FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            return {"success": False, "message": "User not found"}
        
        # Get the password hash
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        stored_password = cursor.fetchone()[0]
        
        hashed_input = hash_password(password)
        if stored_password == hashed_input:
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user[0],
                    "name": user[1],
                    "role": user[2],
                    "interests": user[3].split(",") if user[3] else []
                }
            }
        else:
            return {"success": False, "message": "Invalid password"}
    except Exception as e:
        return {"success": False, "message": str(e)}