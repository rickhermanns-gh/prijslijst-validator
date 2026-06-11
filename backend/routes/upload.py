"""
PDF Upload route
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
import os
import uuid
from pathlib import Path
from datetime import datetime
from main import sessions_db

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

class UploadResponse(BaseModel):
    session_id: str
    supplier: str
    file_name: str
    status: str
    created_at: str

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    supplier: str = Form(...),
):
    """Upload PDF and create session"""

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Validate file size (max 100MB)
    max_size = 100 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 100MB)",
        )

    # Create session ID
    session_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File save failed",
        )

    # Store session info
    sessions_db[session_id] = {
        "supplier": supplier,
        "file_name": file.filename,
        "file_path": str(file_path),
        "status": "uploaded",
        "created_at": datetime.now().isoformat(),
    }

    return UploadResponse(
        session_id=session_id,
        supplier=supplier,
        file_name=file.filename,
        status="uploaded",
        created_at=datetime.now().isoformat(),
    )
