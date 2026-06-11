"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import bcrypt
from datetime import datetime

router = APIRouter()

# Mock database
users_db = {
    "demo": {
        "id": "user-123",
        "username": "demo",
        "password_hash": bcrypt.hashpw(b"demo", bcrypt.gensalt()).decode(),
        "email": "demo@example.com",
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    id: str
    username: str
    email: str
    token: str

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    user = users_db.get(request.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not bcrypt.checkpw(request.password.encode(), user["password_hash"].encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Generate token (simplified - use JWT in production)
    token = f"token_{user['id']}_{datetime.now().timestamp()}"

    return LoginResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        token=token,
    )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"status": "logged out"}
