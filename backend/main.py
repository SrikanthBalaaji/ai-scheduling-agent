from fastapi import FastAPI

from routes import events, chat, profile, calendar
from db.database import seed_events


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(calendar.router)

seed_events()


@app.get("/")
def root():
    return {"message": "Backend is running"}