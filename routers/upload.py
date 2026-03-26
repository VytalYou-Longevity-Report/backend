"""
VYTALYOU™ Upload Router
Handles file upload, validation, and storage.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from dotenv import load_dotenv

from models.schemas import UploadResponse

load_dotenv()

router = APIRouter(prefix="/api", tags=["Upload"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "20")) * 1024 * 1024  # Convert to bytes
ALLOWED_EXTENSIONS = {".pdf"}


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {ext}. Only PDF files are accepted."
        )


async def save_file(file: UploadFile, session_dir: str, prefix: str) -> str:
    """Save uploaded file to session directory."""
    ext = Path(file.filename).suffix.lower()
    filename = f"{prefix}{ext}"
    filepath = os.path.join(session_dir, filename)

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename} exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    with open(filepath, "wb") as f:
        f.write(content)

    return filepath


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    blood_report: UploadFile = File(..., description="Blood / Lab report PDF"),
    imaging_report: UploadFile = File(None, description="Imaging / Clinical report PDF"),
    inbody_report: UploadFile = File(None, description="InBody / Body composition report PDF"),
):
    """
    Upload medical report PDFs for longevity analysis.

    Required: blood_report (lab work)
    Optional: imaging_report, inbody_report
    """
    # Generate session ID
    session_id = str(uuid.uuid4())

    # Create session directory
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    files_received = []

    try:
        # Validate and save blood report (required)
        validate_file(blood_report)
        await save_file(blood_report, session_dir, "blood_report")
        files_received.append(blood_report.filename)

        # Validate and save imaging report (optional)
        if imaging_report and imaging_report.filename:
            validate_file(imaging_report)
            await save_file(imaging_report, session_dir, "imaging_report")
            files_received.append(imaging_report.filename)

        # Validate and save InBody report (optional)
        if inbody_report and inbody_report.filename:
            validate_file(inbody_report)
            await save_file(inbody_report, session_dir, "inbody_report")
            files_received.append(inbody_report.filename)

    except HTTPException:
        # Clean up on validation failure
        shutil.rmtree(session_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")

    return UploadResponse(
        session_id=session_id,
        files_received=files_received,
        message=f"Successfully uploaded {len(files_received)} file(s). Ready for extraction.",
    )
