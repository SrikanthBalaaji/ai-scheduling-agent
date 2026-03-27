from fastapi import APIRouter
from db.database import cursor
from schemas import Event

router = APIRouter()   # 🔥 THIS WAS MISSING


@router.get("/events")
def get_events(date: str = None, tag: str = None):
    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if date:
        query += " AND date=?"
        params.append(date)

    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return [
        Event(
         id=r[0],
         title=r[1],
         date=r[2],
         start_time=r[3],
         end_time=r[4],
         tags=r[5].split(","),
         campus=r[6]   
)
        for r in rows
    ]