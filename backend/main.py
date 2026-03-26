from fastapi import FastAPI
from backend.routes.calendar import router as calendar_router

app = FastAPI()

# Root check
@app.get("/")
def home():
    return {"message": "Server is running"}

# Include your calendar module
app.include_router(calendar_router)