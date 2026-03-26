"""
VYTALYOU™ Analyze Router
Handles LLM analysis, risk projections, and report generation.
"""

import os
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from models.schemas import (
    AnalysisResponse, FullReportResponse,
    ExtractedPatientData, DerivedMetrics,
)
from services.pdf_extractor import pdf_extractor
from services.metrics import metrics_calculator
from services.llm_engine import llm_engine
from services.risk_engine import risk_engine
from services.pdf_generator import pdf_generator

router = APIRouter(prefix="/api", tags=["Analysis"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

# In-memory session store (use Redis in production)
_session_store = {}


@router.post("/analyze/{session_id}", response_model=AnalysisResponse)
async def analyze(session_id: str):
    """
    Run the full analysis pipeline:
    1. Extract data from PDFs
    2. Compute derived metrics
    3. Generate LLM longevity report
    4. Compute risk projections
    5. Generate physician sheet
    """
    session_dir = os.path.join(UPLOAD_DIR, session_id)

    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        # Stage 1: Extract
        blood_path = os.path.join(session_dir, "blood_report.pdf")
        imaging_path = os.path.join(session_dir, "imaging_report.pdf")
        inbody_path = os.path.join(session_dir, "inbody_report.pdf")

        extracted_data = pdf_extractor.extract_from_files(
            blood_report_path=blood_path if os.path.exists(blood_path) else None,
            imaging_report_path=imaging_path if os.path.exists(imaging_path) else None,
            inbody_report_path=inbody_path if os.path.exists(inbody_path) else None,
        )

        # Stage 2: Compute derived metrics
        derived_metrics = metrics_calculator.compute(extracted_data)

        # Stage 3 + 6: LLM analysis (report + physician sheet)
        report, physician_sheet = await llm_engine.generate_full_analysis(
            extracted_data, derived_metrics
        )

        # Stage 4: Risk projections
        risk_projection = risk_engine.compute_projections(
            extracted_data, derived_metrics
        )

        # Store results for later use
        _session_store[session_id] = {
            "extracted_data": extracted_data,
            "derived_metrics": derived_metrics,
            "report": report,
            "physician_sheet": physician_sheet,
            "risk_projection": risk_projection,
        }

        return AnalysisResponse(
            session_id=session_id,
            report=report,
            risk_projection=risk_projection,
            physician_sheet=physician_sheet,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/generate-report/{session_id}")
async def generate_report(session_id: str):
    """
    Generate the full HTML/PDF report for download.
    Must call /analyze first.
    """
    if session_id not in _session_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis results not found. Please run /analyze first."
        )

    try:
        data = _session_store[session_id]

        # Stage 7: Generate PDF/HTML report
        html = pdf_generator.generate_report_html(
            report=data["report"],
            physician_sheet=data["physician_sheet"],
            risk_projection=data["risk_projection"],
            patient_data=data["extracted_data"],
            derived_metrics=data["derived_metrics"],
            session_id=session_id,
        )

        # Save the HTML report
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        filepath = pdf_generator.save_report(html, session_dir, session_id)

        return {
            "session_id": session_id,
            "report_url": f"/api/download-report/{session_id}",
            "message": "Report generated successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@router.get("/download-report/{session_id}")
async def download_report(session_id: str):
    """Download the generated HTML report."""
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    filepath = os.path.join(session_dir, f"report_{session_id}.html")

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Report not found. Please generate the report first."
        )

    return FileResponse(
        filepath,
        media_type="text/html",
        filename=f"VYTALYOU_Longevity_Report_{session_id[:8]}.html",
    )


@router.get("/full-report/{session_id}", response_model=FullReportResponse)
async def get_full_report(session_id: str):
    """Get complete report data (for frontend dashboard rendering)."""
    if session_id not in _session_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis results not found. Please run /analyze first."
        )

    data = _session_store[session_id]

    return FullReportResponse(
        session_id=session_id,
        report=data["report"],
        risk_projection=data["risk_projection"],
        physician_sheet=data["physician_sheet"],
        extracted_data=data["extracted_data"],
        derived_metrics=data["derived_metrics"],
        pdf_url=f"/api/download-report/{session_id}",
    )
