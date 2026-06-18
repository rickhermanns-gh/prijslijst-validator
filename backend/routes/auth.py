"""
Authentication routes
JWT tokens, bcrypt passwords, rate limiting, httpOnly cookies
"""

from fastapi import APIRouter, HTTPException, status, Request, Response, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
from slowapi import Limiter
from slowapi.util import get_remote_address
from db import get_db
from models import User
from middleware.auth import create_access_token, create_refresh_token

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

ACCESS_TOKEN_EXPIRE_MINUTES = 15


# ─── Schemas ────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    username: str
    email: str


# ─── Endpoints ──────────────────────────────

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/15minutes")  # max 5 pogingen per 15 min per IP
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login: valideert credentials, zet JWT in httpOnly cookie.
    Rate limited: 5 pogingen per 15 minuten per IP.
    """
    user = db.query(User).filter(User.username == body.username).first()

    # Timing-safe: altijd bcrypt draaien om timing attacks te voorkomen
    dummy_hash = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()
    password_hash = user.password_hash if user else dummy_hash

    valid = bcrypt.checkpw(body.password.encode(), password_hash.encode())

    if not user or not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ongeldige gebruikersnaam of wachtwoord",
        )

    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Zet tokens als httpOnly cookies — nooit in response body
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,       # alleen over HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 dagen
        path="/api/auth/refresh",   # alleen voor refresh endpoint
    )

    return LoginResponse(username=user.username, email=user.email or "")


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    """Vernieuw access token via refresh token cookie."""
    from jose import JWTError, jwt
    from middleware.auth import SECRET_KEY, ALGORITHM, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geen refresh token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ongeldig token type")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verlopen of ongeldig token")

    access_token = create_access_token({"sub": payload["sub"], "username": payload["username"]})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"status": "ok"}


@router.post("/logout")
async def logout(response: Response):
    """Verwijder auth cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"status": "uitgelogd"}
