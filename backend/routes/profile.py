from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Pydantic model (keep it here, not in separate models folder)
class StudentProfile(BaseModel):
    user_id: str
    major: str = ""
    year: int = 1
    interests: List[str] = []
    career_goals: List[str] = []

# In-memory storage
PROFILES = {}

@router.post("/profile")
def create_profile(profile: StudentProfile):
    PROFILES[profile.user_id] = profile.dict()
    return {"status": "success", "user_id": profile.user_id}

@router.get("/profile/{user_id}")
def get_profile(user_id: str):
    if user_id not in PROFILES:
        return {
            "user_id": user_id,
            "major": "",
            "year": 1,
            "interests": [],
            "career_goals": []
        }
    return PROFILES[user_id]