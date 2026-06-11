"""
Prijslijst Validator - FastAPI Backend
Interactive pricelist validation tool for 100% spec completion
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Session storage (global, shared across all routes)
sessions_db = {}

# Import routes (after defining sessions_db!)
from routes import auth, upload, scan

# Create app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Prijslijst Validator starting up...")
    yield
    # Shutdown
    print("🛑 Shutting down...")

app = FastAPI(
    title="Prijslijst Validator API",
    description="Backend for interactive pricelist validation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(scan.router, prefix="/api", tags=["scan"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
