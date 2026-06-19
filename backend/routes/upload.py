"""
PDF Upload route — beveiligd met JWT auth
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import uuid
from pathlib import Path
from datetime import datetime
from db import get_db
from models import UploadSession
from middleware.auth import get_current_user
from middleware.audit import log_action

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "application/octet-stream",  # browser stuurt dit soms voor xlsx
}

PDF_MAGIC_BYTES  = b"%PDF"
XLSX_MAGIC_BYTES = b"PK\x03\x04"  # ZIP-based formaat (OOXML)


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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload PDF en maak sessie aan. Vereist ingelogde gebruiker."""

    content = await file.read()

    # Valideer file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestand te groot (max 100MB)",
        )

    # Detecteer bestandstype op magic bytes (niet content-type header — die is onbetrouwbaar)
    is_pdf  = content.startswith(PDF_MAGIC_BYTES)
    is_xlsx = content.startswith(XLSX_MAGIC_BYTES)

    if not is_pdf and not is_xlsx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alleen PDF en XLSX bestanden zijn toegestaan",
        )

    # Sanitize bestandsnaam
    original_name = Path(file.filename).name if file.filename else ("upload.pdf" if is_pdf else "upload.xlsx")
    safe_filename = original_name
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

    # Sla sessie op in PostgreSQL (persistent over server restarts)
    session = UploadSession(
        id=uuid.UUID(session_id),
        user_id=uuid.UUID(current_user["user_id"]),
        supplier=supplier,
        file_name=safe_filename,
        file_path=str(file_path),
        status="uploaded",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    await log_action(
        request,
        action="upload",
        user_id=current_user["user_id"],
        resource_type="upload_session",
        resource_id=session_id,
        metadata={"supplier": supplier, "file_name": safe_filename},
        db=db,
    )

    return UploadResponse(
        session_id=session_id,
        supplier=supplier,
        file_name=safe_filename,
        status="uploaded",
        created_at=session.created_at.isoformat() if session.created_at else datetime.now().isoformat(),
    )
