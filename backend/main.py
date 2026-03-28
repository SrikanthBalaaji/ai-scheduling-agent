from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import events, chat, profile, calendar, auth
from db.database import seed_events


app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(calendar.router)
app.include_router(auth.router)

seed_events()


@app.get("/")
def root():
    return {"message": "Backend is running"}