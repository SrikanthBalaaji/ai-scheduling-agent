from fastapi import FastAPI
from routes import events, chat, profile

app = FastAPI()

app.include_router(events.router)
app.include_router(chat.router)
app.include_router(profile.router, prefix="/profile")

@app.get("/")
def root():
    return {"message": "Backend is running"}