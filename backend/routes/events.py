import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from db.database import cursor
from schemas import Event

router = APIRouter()   # 🔥 THIS WAS MISSING


class EventUpsert(BaseModel):
    title: str
    date: str
    start_time: str
    end_time: str
    tags: List[str] = []
    campus: str = "Main"
    description: str = ""
    club_name: str = ""
    location: str = ""
    mode: str = "offline"
    event_type: str = "event"
    poster_url: str = ""
    google_form_url: str = ""


def _row_to_event(row) -> Event:
    return Event(
        id=row[0],
        title=row[1],
        date=row[2],
        start_time=row[3],
        end_time=row[4],
        tags=row[5].split(",") if row[5] else [],
        campus=row[6] if len(row) > 6 and row[6] else "Main",
        description=row[7] if len(row) > 7 and row[7] else "",
        club_name=row[8] if len(row) > 8 and row[8] else "",
        location=row[9] if len(row) > 9 and row[9] else "",
        mode=row[10] if len(row) > 10 and row[10] else "offline",
        event_type=row[11] if len(row) > 11 and row[11] else "event",
        poster_url=row[12] if len(row) > 12 and row[12] else "",
        google_form_url=row[13] if len(row) > 13 and row[13] else "",
    )


@router.get("/events")
def get_events(date: str = None, tag: str = None):
    query = """
        SELECT id, title, date, start_time, end_time, tags, campus, description,
               club_name, location, mode, event_type, poster_url, google_form_url
        FROM events
        WHERE 1=1
    """
    params = []

    if date:
        query += " AND date=?"
        params.append(date)

    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [_row_to_event(r) for r in rows]


@router.post("/events", response_model=Event)
def create_event(payload: EventUpsert):
    event_id = uuid.uuid4().hex
    cursor.execute(
        """
        INSERT INTO events (
            id, title, date, start_time, end_time, tags, campus, description,
            club_name, location, mode, event_type, poster_url, google_form_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            payload.title,
            payload.date,
            payload.start_time,
            payload.end_time,
            ",".join(payload.tags),
            payload.campus,
            payload.description,
            payload.club_name,
            payload.location,
            payload.mode,
            payload.event_type,
            payload.poster_url,
            payload.google_form_url,
        ),
    )
    cursor.connection.commit()

    cursor.execute(
        """
        SELECT id, title, date, start_time, end_time, tags, campus, description,
               club_name, location, mode, event_type, poster_url, google_form_url
        FROM events WHERE id=?
        """,
        (event_id,),
    )
    row = cursor.fetchone()
    return _row_to_event(row)


@router.put("/events/{event_id}", response_model=Event)
def update_event(event_id: str, payload: EventUpsert):
    cursor.execute(
        """
        UPDATE events
        SET title=?, date=?, start_time=?, end_time=?, tags=?, campus=?, description=?,
            club_name=?, location=?, mode=?, event_type=?, poster_url=?, google_form_url=?
        WHERE id=?
        """,
        (
            payload.title,
            payload.date,
            payload.start_time,
            payload.end_time,
            ",".join(payload.tags),
            payload.campus,
            payload.description,
            payload.club_name,
            payload.location,
            payload.mode,
            payload.event_type,
            payload.poster_url,
            payload.google_form_url,
            event_id,
        ),
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found")

    cursor.connection.commit()
    cursor.execute(
        """
        SELECT id, title, date, start_time, end_time, tags, campus, description,
               club_name, location, mode, event_type, poster_url, google_form_url
        FROM events WHERE id=?
        """,
        (event_id,),
    )
    row = cursor.fetchone()
    return _row_to_event(row)


@router.delete("/events/{event_id}")
def delete_event(event_id: str):
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    cursor.connection.commit()
    return {"success": True}