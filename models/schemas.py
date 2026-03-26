"""
VYTALYOU™ Longevity Engine — Pydantic Data Models
All structured data schemas for the multi-stage pipeline.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ─── STAGE 1: Extracted Patient Data ──────────────────────────────────────────

class PatientInfo(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    name: Optional[str] = None
    date_of_report: Optional[str] = None


class LabValues(BaseModel):
    hba1c: Optional[float] = Field(None, description="Glycated Hemoglobin (%)")
    fasting_glucose: Optional[float] = Field(None, description="Fasting Blood Sugar (mg/dL)")
    post_prandial_glucose: Optional[float] = Field(None, description="Post-Prandial Glucose (mg/dL)")
    fasting_insulin: Optional[float] = Field(None, description="Fasting Insulin (µIU/mL)")
    creatinine: Optional[float] = Field(None, description="Serum Creatinine (mg/dL)")
    egfr: Optional[float] = Field(None, description="Estimated GFR (mL/min/1.73m²)")
    bun: Optional[float] = Field(None, description="Blood Urea Nitrogen (mg/dL)")
    uric_acid: Optional[float] = Field(None, description="Uric Acid (mg/dL)")
    albumin: Optional[float] = Field(None, description="Serum Albumin (g/dL)")
    hemoglobin: Optional[float] = Field(None, description="Hemoglobin (g/dL)")
    wbc: Optional[float] = Field(None, description="White Blood Cell Count (×10³/µL)")
    platelet_count: Optional[float] = Field(None, description="Platelet Count (×10³/µL)")
    tsh: Optional[float] = Field(None, description="Thyroid Stimulating Hormone (mIU/L)")
    free_t4: Optional[float] = Field(None, description="Free Thyroxine (ng/dL)")
    vitamin_d: Optional[float] = Field(None, description="25-OH Vitamin D (ng/mL)")
    vitamin_b12: Optional[float] = Field(None, description="Vitamin B12 (pg/mL)")
    ferritin: Optional[float] = Field(None, description="Ferritin (ng/mL)")
    iron: Optional[float] = Field(None, description="Serum Iron (µg/dL)")


class LipidProfile(BaseModel):
    total_cholesterol: Optional[float] = Field(None, description="Total Cholesterol (mg/dL)")
    ldl: Optional[float] = Field(None, description="LDL Cholesterol (mg/dL)")
    hdl: Optional[float] = Field(None, description="HDL Cholesterol (mg/dL)")
    triglycerides: Optional[float] = Field(None, description="Triglycerides (mg/dL)")
    vldl: Optional[float] = Field(None, description="VLDL Cholesterol (mg/dL)")
    lp_a: Optional[float] = Field(None, description="Lipoprotein(a) (nmol/L)")
    apob: Optional[float] = Field(None, description="Apolipoprotein B (mg/dL)")


class LiverPanel(BaseModel):
    sgot_ast: Optional[float] = Field(None, description="AST/SGOT (U/L)")
    sgpt_alt: Optional[float] = Field(None, description="ALT/SGPT (U/L)")
    ggt: Optional[float] = Field(None, description="GGT (U/L)")
    alp: Optional[float] = Field(None, description="Alkaline Phosphatase (U/L)")
    total_bilirubin: Optional[float] = Field(None, description="Total Bilirubin (mg/dL)")
    direct_bilirubin: Optional[float] = Field(None, description="Direct Bilirubin (mg/dL)")
    fatty_liver_grade: Optional[str] = Field(None, description="Fatty Liver Grade (None/I/II/III)")
    fibroscan_kpa: Optional[float] = Field(None, description="FibroScan stiffness (kPa)")
    cap_score: Optional[float] = Field(None, description="CAP Score (dB/m)")
    tai: Optional[float] = Field(None, description="Tissue Attenuation Imaging")


class InflammationMarkers(BaseModel):
    crp: Optional[float] = Field(None, description="C-Reactive Protein (mg/L)")
    hs_crp: Optional[float] = Field(None, description="High-Sensitivity CRP (mg/L)")
    esr: Optional[float] = Field(None, description="Erythrocyte Sedimentation Rate (mm/hr)")
    il6: Optional[float] = Field(None, description="Interleukin-6 (pg/mL)")
    tnf_alpha: Optional[float] = Field(None, description="TNF-alpha (pg/mL)")
    homocysteine: Optional[float] = Field(None, description="Homocysteine (µmol/L)")


class InBodyMetrics(BaseModel):
    weight: Optional[float] = Field(None, description="Weight (kg)")
    height: Optional[float] = Field(None, description="Height (cm)")
    bmi: Optional[float] = Field(None, description="Body Mass Index")
    body_fat_percentage: Optional[float] = Field(None, description="Percent Body Fat (%)")
    skeletal_muscle_mass: Optional[float] = Field(None, description="Skeletal Muscle Mass (kg)")
    visceral_fat_area: Optional[float] = Field(None, description="Visceral Fat Area (cm²)")
    visceral_fat_level: Optional[float] = Field(None, description="Visceral Fat Level")
    basal_metabolic_rate: Optional[float] = Field(None, description="BMR (kcal)")
    total_body_water: Optional[float] = Field(None, description="Total Body Water (L)")
    phase_angle: Optional[float] = Field(None, description="Phase Angle (degrees)")
    ecw_tbw_ratio: Optional[float] = Field(None, description="ECW/TBW Ratio")
    smi: Optional[float] = Field(None, description="Skeletal Muscle Index (kg/m²)")


class CardiacFindings(BaseModel):
    systolic_bp: Optional[int] = Field(None, description="Systolic Blood Pressure (mmHg)")
    diastolic_bp: Optional[int] = Field(None, description="Diastolic Blood Pressure (mmHg)")
    heart_rate: Optional[int] = Field(None, description="Resting Heart Rate (bpm)")
    ejection_fraction: Optional[float] = Field(None, description="Ejection Fraction (%)")
    lvef: Optional[float] = Field(None, description="LV Ejection Fraction (%)")
    e_a_ratio: Optional[float] = Field(None, description="E/A Ratio")
    lv_mass_index: Optional[float] = Field(None, description="LV Mass Index (g/m²)")
    calcium_score: Optional[float] = Field(None, description="Coronary Calcium Score")
    ecg_findings: Optional[str] = Field(None, description="ECG Summary")
    echo_findings: Optional[str] = Field(None, description="Echocardiography Summary")
    diastolic_dysfunction: Optional[str] = Field(None, description="Diastolic Dysfunction Grade")


class ExtractedPatientData(BaseModel):
    """Complete extracted patient data from all uploaded documents."""
    patient: PatientInfo = Field(default_factory=PatientInfo)
    labs: LabValues = Field(default_factory=LabValues)
    lipids: LipidProfile = Field(default_factory=LipidProfile)
    liver: LiverPanel = Field(default_factory=LiverPanel)
    inflammation: InflammationMarkers = Field(default_factory=InflammationMarkers)
    inbody: InBodyMetrics = Field(default_factory=InBodyMetrics)
    cardiac: CardiacFindings = Field(default_factory=CardiacFindings)
    raw_text: str = Field("", description="Raw unstructured text from all PDFs combined for full analytical context.")


# ─── STAGE 2: Derived Longevity Metrics ──────────────────────────────────────

class RiskCategory(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"
    CRITICAL = "Critical"


class DerivedMetrics(BaseModel):
    homa_ir: Optional[float] = Field(None, description="HOMA-IR = (Fasting Insulin × FBS) / 405")
    homa_ir_risk: Optional[RiskCategory] = None
    tg_hdl_ratio: Optional[float] = Field(None, description="Triglyceride/HDL ratio")
    tg_hdl_risk: Optional[RiskCategory] = None
    tyg_index: Optional[float] = Field(None, description="TyG Index = ln(TG × FBS / 2)")
    tyg_risk: Optional[RiskCategory] = None
    visceral_fat_risk: Optional[RiskCategory] = None
    sarcopenia_index: Optional[float] = Field(None, description="SMI-based Sarcopenia Index")
    sarcopenia_risk: Optional[RiskCategory] = None
    biological_age_drift: Optional[float] = Field(None, description="Biological Age - Chronological Age")
    estimated_biological_age: Optional[float] = None
    inflammation_composite: Optional[float] = Field(None, description="Composite inflammation score")
    metabolic_syndrome_score: Optional[int] = Field(None, description="Number of MetS criteria met (0-5)")


# ─── STAGE 3: LLM Report Output ─────────────────────────────────────────────

class LongevityReport(BaseModel):
    markdown: str


# ─── STAGE 4: Risk Projections ───────────────────────────────────────────────

class RiskDataPoint(BaseModel):
    year: int
    risk_index: float


class RiskProjection(BaseModel):
    mortality_curve: List[RiskDataPoint]
    morbidity_curve: List[RiskDataPoint]
    baseline_mortality: List[RiskDataPoint]
    baseline_morbidity: List[RiskDataPoint]


# ─── STAGE 6: Physician Sheet ───────────────────────────────────────────────

class PhysicianFinding(BaseModel):
    domain: str
    finding: str
    clinical_meaning: str
    urgency: str  # Routine / Monitor / Urgent / Critical


class PhysicianSheet(BaseModel):
    patient_summary: str
    findings: List[PhysicianFinding]
    priorities: List[str]
    follow_up_timeline: str


# ─── API Response Models ─────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    session_id: str
    files_received: List[str]
    message: str


class ExtractionResponse(BaseModel):
    session_id: str
    extracted_data: ExtractedPatientData
    derived_metrics: DerivedMetrics


class AnalysisResponse(BaseModel):
    session_id: str
    report: LongevityReport
    risk_projection: RiskProjection
    physician_sheet: PhysicianSheet


class FullReportResponse(BaseModel):
    session_id: str
    report: LongevityReport
    risk_projection: RiskProjection
    physician_sheet: PhysicianSheet
    extracted_data: ExtractedPatientData
    derived_metrics: DerivedMetrics
    pdf_url: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
