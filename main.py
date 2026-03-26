"""
VYTALYOU™ Ultra Precision Longevity Engine — FastAPI Application
Main entry point for the backend API.
"""

import os
import uuid
import shutil
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from models.schemas import (
    ExtractedPatientData, DerivedMetrics,
    LongevityReport, RiskProjection, PhysicianSheet,
    UploadResponse, ExtractionResponse, AnalysisResponse,
    FullReportResponse, ErrorResponse,
    RiskDataPoint,
)
from services.pdf_extractor import pdf_extractor
from services.metrics import metrics_calculator
from services.llm_engine import llm_engine
from services.risk_engine import risk_engine
from services.pdf_generator import pdf_generator
from routers.upload import router as upload_router

load_dotenv()

app = FastAPI(
    title="VYTALYOU™ Ultra Precision Longevity Engine",
    description="AI-powered longevity analysis from medical reports",
    version="1.0.0",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the upload router
app.include_router(upload_router)

# In-memory session store (use Redis/DB in production)
sessions: dict = {}

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {"status": "online", "engine": "VYTALYOU™ Ultra Precision Longevity Engine v1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/upload-and-store", response_model=UploadResponse)
async def upload_reports(
    laboratory_report: UploadFile = File(None),
    radiology_report: UploadFile = File(None),
    excel_report: UploadFile = File(None),
):
    """Upload medical reports for analysis."""
    if not radiology_report or (not laboratory_report and not excel_report):
        raise HTTPException(status_code=400, detail="Radiology report and either a laboratory or an excel report are required.")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    files_received = []
    file_paths = {}

    for label, upload_file in [
        ("laboratory_report", laboratory_report),
        ("radiology_report", radiology_report),
        ("excel_report", excel_report),
    ]:
        if not upload_file or not upload_file.filename:
            continue

        if label == "excel_report":
            if not upload_file.filename.endswith((".xlsx", ".xls")):
                raise HTTPException(status_code=400, detail=f"A valid Excel file is required for {label}.")
            ext = os.path.splitext(upload_file.filename)[1]
            filepath = os.path.join(session_dir, f"{label}{ext}")
        else:
            if not upload_file.filename.endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"A valid PDF is required for {label}.")
            filepath = os.path.join(session_dir, f"{label}.pdf")

        with open(filepath, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        file_paths[label] = filepath
        files_received.append(upload_file.filename)

    sessions[session_id] = {"file_paths": file_paths, "status": "uploaded"}

    return UploadResponse(
        session_id=session_id,
        files_received=files_received,
        message=f"Successfully uploaded {len(files_received)} report(s). Ready for analysis.",
    )


@app.post("/api/extract/{session_id}", response_model=ExtractionResponse)
async def extract_data(session_id: str):
    """Stage 1 & 2: Extract data from PDFs and compute derived metrics."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[session_id]
    paths = session["file_paths"]

    # Stage 1: Extraction
    extracted = pdf_extractor.extract_from_files(
        laboratory_report_path=paths.get("laboratory_report"),
        radiology_report_path=paths.get("radiology_report"),
        excel_report_path=paths.get("excel_report"),
    )

    # Stage 2: Derived Metrics
    metrics = metrics_calculator.compute(extracted)

    session["extracted_data"] = extracted
    session["derived_metrics"] = metrics
    session["status"] = "extracted"

    return ExtractionResponse(
        session_id=session_id,
        extracted_data=extracted,
        derived_metrics=metrics,
    )


@app.post("/api/analyze/{session_id}", response_model=AnalysisResponse)
async def analyze(session_id: str):
    """Stage 3+: Generate LLM-based longevity report and physician sheet."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[session_id]
    if "extracted_data" not in session:
        raise HTTPException(status_code=400, detail="Please run extraction first.")

    data = session["extracted_data"]
    metrics = session["derived_metrics"]

    # Stage 3: LLM Analysis
    report, physician_sheet = await llm_engine.generate_full_analysis(data, metrics)

    # Stage 4: Risk Projections
    risk_projection = risk_engine.compute_projections(data, metrics)

    session["report"] = report
    session["risk_projection"] = risk_projection
    session["physician_sheet"] = physician_sheet
    session["status"] = "analyzed"

    return AnalysisResponse(
        session_id=session_id,
        report=report,
        risk_projection=risk_projection,
        physician_sheet=physician_sheet,
    )


@app.post("/api/full-report/{session_id}", response_model=FullReportResponse)
async def full_report(session_id: str):
    """Run the complete pipeline: extract → compute → analyze → report."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Run extraction
    await extract_data(session_id)
    # Run analysis
    await analyze(session_id)

    session = sessions[session_id]

    return FullReportResponse(
        session_id=session_id,
        report=session["report"],
        risk_projection=session["risk_projection"],
        physician_sheet=session["physician_sheet"],
        extracted_data=session["extracted_data"],
        derived_metrics=session["derived_metrics"],
    )


@app.get("/api/report/{session_id}/html", response_class=HTMLResponse)
async def get_report_html(session_id: str):
    """Get the generated HTML report for viewing/printing as PDF."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = sessions[session_id]
    if "report" not in session:
        raise HTTPException(status_code=400, detail="Report not generated yet. Run full-report first.")

    html = pdf_generator.generate_report_html(
        report=session["report"],
        physician_sheet=session["physician_sheet"],
        risk_projection=session["risk_projection"],
        patient_data=session["extracted_data"],
        derived_metrics=session["derived_metrics"],
        session_id=session_id,
    )

    return HTMLResponse(content=html)
