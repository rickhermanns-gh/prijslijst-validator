"""
Prijslijst Validator - FastAPI Backend
Interactive pricelist validation tool for 100% spec completion
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Routes ─────────────────────────────────────────────────────────────────
from routes import auth, upload, scan

# ─── Rate limiter ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ─── CORS origins uit environment ────────────────────────────────────────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]


def _seed_demo_user():
    """Zet demo user in de DB als die nog niet bestaat."""
    from db import SessionLocal
    from models import User
    import bcrypt

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "demo").first()
        if not existing:
            hashed = bcrypt.hashpw(b"demo", bcrypt.gensalt()).decode()
            demo_user = User(
                username="demo",
                email="demo@example.com",
                password_hash=hashed,
            )
            db.add(demo_user)
            db.commit()
            print("   ✅ Demo user aangemaakt (username: demo)")
        else:
            print("   ✅ Demo user bestaat al")
    except Exception as e:
        db.rollback()
        print(f"   ⚠️  Demo user seeding mislukt: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Prijslijst Validator starting up...")
    print(f"   CORS allowed origins: {ALLOWED_ORIGINS}")

    # DB tabellen aanmaken (CREATE TABLE IF NOT EXISTS)
    from db import engine, Base
    import models  # nodig zodat Base de tabellen kent  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("   ✅ Database tabellen geverifieerd")

    _seed_demo_user()

    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="Prijslijst Validator API",
    description="Backend for interactive pricelist validation",
    version="1.0.0",
    lifespan=lifespan,
    # Verberg docs in productie
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url=None,
)

# ─── Rate limit handler ──────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS — strikt, geen wildcard ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ─── Health check ────────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(scan.router, prefix="/api/scan", tags=["scan"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
