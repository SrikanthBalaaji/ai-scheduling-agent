from fastapi import APIRouter

router = APIRouter()

@router.get("/events")
def get_events():
    return [
        {
            "id": "1",
            "title": "Hackathon",
            "club": "Coding Club",
            "description": "24hr coding event",
            "date": "2026-03-30",
            "start_time": "10:00",
            "end_time": "18:00",
            "location": "Auditorium",
            "tags": ["tech"],
            "registration_url": "https://example.com"
        },
        {
            "id": "2",
            "title": "Music Night",
            "club": "Cultural Club",
            "description": "Live performances",
            "date": "2026-03-30",
            "start_time": "17:00",
            "end_time": "20:00",
            "location": "Main Stage",
            "tags": ["cultural"],
            "registration_url": "https://example.com"
        }
    ]