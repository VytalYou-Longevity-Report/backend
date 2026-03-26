"""
VYTALYOU™ Extract Router
Handles PDF extraction and derived metric computation.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import ExtractionResponse
from services.pdf_extractor import pdf_extractor
from services.metrics import metrics_calculator

router = APIRouter(prefix="/api", tags=["Extraction"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


@router.post("/extract/{session_id}", response_model=ExtractionResponse)
async def extract_data(session_id: str):
    """
    Extract structured data from uploaded PDFs and compute derived metrics.
    """
    session_dir = os.path.join(UPLOAD_DIR, session_id)

    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Build file paths
    blood_path = os.path.join(session_dir, "blood_report.pdf")
    imaging_path = os.path.join(session_dir, "imaging_report.pdf")
    inbody_path = os.path.join(session_dir, "inbody_report.pdf")

    # Extract data from available PDFs
    try:
        extracted_data = pdf_extractor.extract_from_files(
            blood_report_path=blood_path if os.path.exists(blood_path) else None,
            imaging_report_path=imaging_path if os.path.exists(imaging_path) else None,
            inbody_report_path=inbody_path if os.path.exists(inbody_path) else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF extraction failed: {str(e)}"
        )

    # Compute derived metrics
    try:
        derived_metrics = metrics_calculator.compute(extracted_data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metrics computation failed: {str(e)}"
        )

    return ExtractionResponse(
        session_id=session_id,
        extracted_data=extracted_data,
        derived_metrics=derived_metrics,
    )
