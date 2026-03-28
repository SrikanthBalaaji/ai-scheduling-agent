from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.database import create_user, login_user
import uuid

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str
    role: str = "student"
    interests: list = []


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/register")
def register(request: RegisterRequest):
    """Register a new user"""
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    
    user_id = str(uuid.uuid4())
    interests_str = ",".join(request.interests) if request.interests else ""
    
    result = create_user(user_id, request.username, request.name, request.password, request.role, interests_str)
    
    if result["success"]:
        return {
            "success": True,
            "message": "Registration successful",
            "user_id": user_id,
            "name": request.name,
            "role": request.role,
            "interests": request.interests
        }
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.post("/auth/login")
def login(request: LoginRequest):
    """Login an existing user"""
    if not request.username or not request.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    result = login_user(request.username, request.password)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=401, detail=result["message"])
