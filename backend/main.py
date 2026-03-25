from fastapi import FastAPI
from routes import events
from routes import chat

app = FastAPI()

# Include routes
app.include_router(events.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {"message": "Backend is running"}