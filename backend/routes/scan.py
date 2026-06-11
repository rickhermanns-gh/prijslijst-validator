"""
PDF Scanning routes - Scan 1, Gap Analysis, Scan 2
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from main import sessions_db

router = APIRouter()

class Scan1Result(BaseModel):
    total_items: int
    items_with_specs: int
    items_complete: int
    completion_percentage: int

class ScanResponse(BaseModel):
    session_id: str
    status: str
    result: Optional[Dict[str, Any]]

class GapAnalysisResponse(BaseModel):
    total_items: int
    complete_items: int
    missing_specs_items: int
    pricing_only_items: int
    completion_percentage: int
    gap_items: List[Dict[str, Any]]

@router.post("/scan1/{session_id}")
async def scan1(session_id: str, background_tasks: BackgroundTasks):
    """
    Scan 1: Automatic extraction using maximum patterns
    (integrates the ZR extraction logic we built)
    """

    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session = sessions_db[session_id]

    # Simulate scan (in production: call actual extraction here)
    # For now: mock result based on ZR data
    result = {
        "total_items": 836,
        "items_with_specs": 717,
        "items_complete": 566,
        "completion_percentage": 68,
        "scan_time_ms": 2340,
    }

    # Mock gap analysis
    gap_analysis = [
        {
            "item_id": "15501",
            "item_name": "Villa Palagonia",
            "missing_fields": ["breedte", "rapport"],
        }
        for _ in range(119)
    ][:10]  # Show first 10

    sessions_db[session_id]["status"] = "scan1_done"
    sessions_db[session_id]["scan1_result"] = result
    sessions_db[session_id]["scan1_started"] = datetime.now().isoformat()

    return {
        "session_id": session_id,
        "supplier": session.get("supplier", "Onbekend"),
        "file_name": session.get("file_name", ""),
        "scan1_items": result["total_items"],
        "scan1_completion": result["completion_percentage"],
        "gap_analysis": gap_analysis,
        "status": "scan1_done",
    }

@router.get("/gap-analysis/{session_id}", response_model=GapAnalysisResponse)
async def gap_analysis(session_id: str):
    """
    Gap Analysis: Show what's missing
    """

    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session = sessions_db[session_id]
    if session["status"] not in ["scan1_done", "scan2_done"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan 1 not completed yet",
        )

    # Mock gap analysis
    gap_items = [
        {
            "item_number": "15501",
            "item_name": "Villa Palagonia",
            "missing_fields": ["breedte", "rapport"],
        }
        for _ in range(119)
    ][:10]  # Show first 10

    return GapAnalysisResponse(
        total_items=836,
        complete_items=566,
        missing_specs_items=119,
        pricing_only_items=151,
        completion_percentage=68,
        gap_items=gap_items,
    )

@router.post("/scan2/{session_id}")
async def scan2(session_id: str):
    """
    Scan 2: Advanced pattern matching for remaining gaps
    """

    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session = sessions_db[session_id]

    # Mock Scan 2 result
    result = {
        "additional_items_found": 45,
        "items_improved": 119,
        "new_completion_percentage": 85,
        "scan_time_ms": 3450,
    }

    sessions_db[session_id]["status"] = "scan2_done"
    sessions_db[session_id]["scan2_result"] = result

    return ScanResponse(
        session_id=session_id,
        status="scan2_done",
        result=result,
    )

@router.post("/validate/{session_id}")
async def validate_item(
    session_id: str,
    item_id: str,
    page_number: int,
    column_ref: str,
):
    """
    Manual validation: User specifies where the specs are
    """

    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Store validation
    if "validations" not in sessions_db[session_id]:
        sessions_db[session_id]["validations"] = []

    sessions_db[session_id]["validations"].append({
        "item_id": item_id,
        "page": page_number,
        "column": column_ref,
        "validated_at": datetime.now().isoformat(),
    })

    return {
        "status": "validated",
        "item_id": item_id,
        "message": "Item validated successfully",
    }

@router.get("/export/{session_id}")
async def export_csv(session_id: str):
    """
    Export 100% complete CSV
    """

    if session_id not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # In production: generate actual CSV from database
    # For now: mock response
    return {
        "download_url": f"/downloads/{session_id}_complete.csv",
        "filename": f"Pricelist_{session_id}_complete.csv",
        "completion": "100%",
        "total_rows": 836,
    }
