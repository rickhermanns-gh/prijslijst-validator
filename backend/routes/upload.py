"""
PDF Upload route — beveiligd met JWT auth
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Request
from pydantic import BaseModel
import os
import uuid
from pathlib import Path
from datetime import datetime
from main import sessions_db
from middleware.auth import get_current_user
from middleware.audit import log_action

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF"


class UploadResponse(BaseModel):
    session_id: str
    supplier: str
    file_name: str
    status: str
    created_at: str


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    supplier: str = Form(...),
    current_user: dict = Depends(get_current_user),  # 🔒 auth vereist
):
    """Upload PDF en maak sessie aan. Vereist ingelogde gebruiker."""

    # Valideer content-type header
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen PDF bestanden zijn toegestaan",
        )

    content = await file.read()

    # Valideer file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestand te groot (max 100MB)",
        )

    # Valideer magic bytes — voorkomt content-type spoofing
    if not content.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ongeldig bestandsformaat",
        )

    # Sanitize bestandsnaam — geen path traversal
    safe_filename = Path(file.filename).name if file.filename else "upload.pdf"
    session_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{session_id}_{safe_filename}"

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Opslaan mislukt",
        )

    now = datetime.now().isoformat()
    sessions_db[session_id] = {
        "user_id": current_user["user_id"],
        "supplier": supplier,
        "file_name": safe_filename,
        "file_path": str(file_path),
        "status": "uploaded",
        "created_at": now,
    }

    await log_action(
        request,
        action="upload",
        user_id=current_user["user_id"],
        resource_type="upload_session",
        resource_id=session_id,
        metadata={"supplier": supplier, "file_name": safe_filename},
    )

    return UploadResponse(
        session_id=session_id,
        supplier=supplier,
        file_name=safe_filename,
        status="uploaded",
        created_at=now,
    )
