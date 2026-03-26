"""
VYTALYOU™ Stage 1: PDF Extraction Engine
Extracts structured medical data from uploaded PDF reports using pdfplumber + OCR fallback.
"""

import re
import json
import pdfplumber
import fitz  # PyMuPDF
from typing import Optional, Dict, Any, List
from pathlib import Path

from models.schemas import (
    ExtractedPatientData, PatientInfo, LabValues, LipidProfile,
    LiverPanel, InflammationMarkers, InBodyMetrics, CardiacFindings,
)


class PDFExtractor:
    """Multi-strategy PDF extraction with text parsing and OCR fallback."""

    def __init__(self):
        self.lab_patterns = self._build_lab_patterns()
        self.lipid_patterns = self._build_lipid_patterns()
        self.liver_patterns = self._build_liver_patterns()
        self.inflammation_patterns = self._build_inflammation_patterns()
        self.inbody_patterns = self._build_inbody_patterns()
        self.cardiac_patterns = self._build_cardiac_patterns()
        self.patient_patterns = self._build_patient_patterns()

    # ─── PATTERN BUILDERS ─────────────────────────────────────────────

    def _build_patient_patterns(self) -> Dict[str, List[re.Pattern]]:
        return {
            "age": [
                re.compile(r"age\s*[:\-]?\s*(\d{1,3})\s*(?:years?|yrs?|y)?", re.IGNORECASE),
                re.compile(r"(\d{1,3})\s*(?:years?|yrs?)\s*(?:old)?", re.IGNORECASE),
            ],
            "gender": [
                re.compile(r"(?:sex|gender)\s*[:\-]?\s*(male|female|m|f)", re.IGNORECASE),
            ],
            "name": [
                re.compile(r"(?:patient\s*name|name)\s*[:\-]?\s*([A-Za-z\s\.]+?)(?:\n|$|age|sex|gender|dob)", re.IGNORECASE),
            ],
        }

    def _build_lab_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "hba1c": [
                re.compile(rf"(?:hba1c|hb\s*a1c|glycated\s*h(?:a?e)?moglobin|a1c){sep}{num}", re.IGNORECASE),
            ],
            "fasting_glucose": [
                re.compile(rf"(?:fasting\s*(?:blood\s*)?(?:sugar|glucose)|fbs|fbg|fasting\s*plasma\s*glucose|fpg){sep}{num}", re.IGNORECASE),
            ],
            "post_prandial_glucose": [
                re.compile(rf"(?:post\s*prandial|pp\s*(?:blood\s*)?(?:sugar|glucose)|ppbs|ppbg|2\s*hr?\s*(?:glucose|sugar)){sep}{num}", re.IGNORECASE),
            ],
            "fasting_insulin": [
                re.compile(rf"(?:fasting\s*insulin|insulin\s*fasting){sep}{num}", re.IGNORECASE),
            ],
            "creatinine": [
                re.compile(rf"(?:serum\s*)?creatinine{sep}{num}", re.IGNORECASE),
            ],
            "egfr": [
                re.compile(rf"(?:egfr|estimated\s*gfr|glomerular\s*filtration){sep}{num}", re.IGNORECASE),
            ],
            "bun": [
                re.compile(rf"(?:bun|blood\s*urea\s*nitrogen|urea\s*nitrogen){sep}{num}", re.IGNORECASE),
            ],
            "uric_acid": [
                re.compile(rf"uric\s*acid{sep}{num}", re.IGNORECASE),
            ],
            "albumin": [
                re.compile(rf"(?:serum\s*)?albumin{sep}{num}", re.IGNORECASE),
            ],
            "hemoglobin": [
                re.compile(rf"(?:h(?:a?e)?moglobin|hb|hgb){sep}{num}", re.IGNORECASE),
            ],
            "wbc": [
                re.compile(rf"(?:wbc|white\s*blood\s*cell|total\s*(?:wbc|leucocyte)){sep}{num}", re.IGNORECASE),
            ],
            "platelet_count": [
                re.compile(rf"(?:platelet\s*count|platelets|plt){sep}{num}", re.IGNORECASE),
            ],
            "tsh": [
                re.compile(rf"(?:tsh|thyroid\s*stimulating){sep}{num}", re.IGNORECASE),
            ],
            "free_t4": [
                re.compile(rf"(?:free\s*t4|ft4|free\s*thyroxine){sep}{num}", re.IGNORECASE),
            ],
            "vitamin_d": [
                re.compile(rf"(?:vitamin\s*d|25[\s\-]?oh[\s\-]?(?:vitamin\s*)?d|vit[\s\.]?\s*d){sep}{num}", re.IGNORECASE),
            ],
            "vitamin_b12": [
                re.compile(rf"(?:vitamin\s*b[\s\-]?12|vit[\s\.]?\s*b[\s\-]?12|b12|cyanocobalamin){sep}{num}", re.IGNORECASE),
            ],
            "ferritin": [
                re.compile(rf"ferritin{sep}{num}", re.IGNORECASE),
            ],
            "iron": [
                re.compile(rf"(?:serum\s*)?iron{sep}{num}", re.IGNORECASE),
            ],
        }

    def _build_lipid_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "total_cholesterol": [
                re.compile(rf"(?:total\s*cholesterol|t[\.\s]?chol|tc){sep}{num}", re.IGNORECASE),
            ],
            "ldl": [
                re.compile(rf"(?:ldl[\s\-]?(?:cholesterol|c)?|low\s*density){sep}{num}", re.IGNORECASE),
            ],
            "hdl": [
                re.compile(rf"(?:hdl[\s\-]?(?:cholesterol|c)?|high\s*density){sep}{num}", re.IGNORECASE),
            ],
            "triglycerides": [
                re.compile(rf"(?:triglycerides?|tg|trigs?){sep}{num}", re.IGNORECASE),
            ],
            "vldl": [
                re.compile(rf"(?:vldl[\s\-]?(?:cholesterol|c)?|very\s*low\s*density){sep}{num}", re.IGNORECASE),
            ],
            "lp_a": [
                re.compile(rf"(?:lp[\s\(\-]?a[\)\s]?|lipoprotein[\s\(\-]?a[\)\s]?){sep}{num}", re.IGNORECASE),
            ],
            "apob": [
                re.compile(rf"(?:apo[\s\-]?b|apolipoprotein[\s\-]?b){sep}{num}", re.IGNORECASE),
            ],
        }

    def _build_liver_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "sgot_ast": [
                re.compile(rf"(?:sgot|ast|aspartate)\s*[:\-/]?\s*(?:ast|sgot)?{sep}{num}", re.IGNORECASE),
            ],
            "sgpt_alt": [
                re.compile(rf"(?:sgpt|alt|alanine)\s*[:\-/]?\s*(?:alt|sgpt)?{sep}{num}", re.IGNORECASE),
            ],
            "ggt": [
                re.compile(rf"(?:ggt|gamma\s*gt|gamma\s*glutamyl){sep}{num}", re.IGNORECASE),
            ],
            "alp": [
                re.compile(rf"(?:alp|alkaline\s*phosphatase){sep}{num}", re.IGNORECASE),
            ],
            "total_bilirubin": [
                re.compile(rf"(?:total\s*bilirubin|t[\.\s]?bil){sep}{num}", re.IGNORECASE),
            ],
            "direct_bilirubin": [
                re.compile(rf"(?:direct\s*bilirubin|d[\.\s]?bil|conjugated\s*bilirubin){sep}{num}", re.IGNORECASE),
            ],
            "fatty_liver_grade": [
                re.compile(r"(?:fatty\s*liver|hepatic\s*steatosis)\s*[:\-]?\s*(?:grade\s*)?(none|i{1,3}|1|2|3|mild|moderate|severe)", re.IGNORECASE),
            ],
            "fibroscan_kpa": [
                re.compile(rf"(?:fibroscan|liver\s*stiffness|transient\s*elastography){sep}{num}\s*(?:kpa)?", re.IGNORECASE),
            ],
            "cap_score": [
                re.compile(rf"(?:cap\s*(?:score)?|controlled\s*attenuation){sep}{num}", re.IGNORECASE),
            ],
            "tai": [
                re.compile(rf"(?:tai|tissue\s*attenuation\s*imaging){sep}{num}", re.IGNORECASE),
            ],
        }

    def _build_inflammation_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "crp": [
                re.compile(rf"(?<!hs[\s\-])(?:crp|c[\s\-]?reactive\s*protein){sep}{num}", re.IGNORECASE),
            ],
            "hs_crp": [
                re.compile(rf"(?:hs[\s\-]?crp|high[\s\-]?sensitivity\s*crp){sep}{num}", re.IGNORECASE),
            ],
            "esr": [
                re.compile(rf"(?:esr|erythrocyte\s*sedimentation){sep}{num}", re.IGNORECASE),
            ],
            "il6": [
                re.compile(rf"(?:il[\s\-]?6|interleukin[\s\-]?6){sep}{num}", re.IGNORECASE),
            ],
            "tnf_alpha": [
                re.compile(rf"(?:tnf[\s\-]?(?:alpha|α)?|tumor\s*necrosis){sep}{num}", re.IGNORECASE),
            ],
            "homocysteine": [
                re.compile(rf"(?:homocysteine|hcy){sep}{num}", re.IGNORECASE),
            ],
        }

    def _build_inbody_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "weight": [
                re.compile(rf"(?:body\s*)?weight{sep}{num}\s*(?:kg)?", re.IGNORECASE),
            ],
            "height": [
                re.compile(rf"height{sep}{num}\s*(?:cm)?", re.IGNORECASE),
            ],
            "bmi": [
                re.compile(rf"(?:bmi|body\s*mass\s*index){sep}{num}", re.IGNORECASE),
            ],
            "body_fat_percentage": [
                re.compile(rf"(?:percent\s*body\s*fat|body\s*fat\s*(?:percentage|%)|pbf){sep}{num}", re.IGNORECASE),
            ],
            "skeletal_muscle_mass": [
                re.compile(rf"(?:skeletal\s*muscle\s*mass|smm){sep}{num}", re.IGNORECASE),
            ],
            "visceral_fat_area": [
                re.compile(rf"(?:visceral\s*fat\s*area|vfa){sep}{num}", re.IGNORECASE),
            ],
            "visceral_fat_level": [
                re.compile(rf"(?:visceral\s*fat\s*level|vfl){sep}{num}", re.IGNORECASE),
            ],
            "basal_metabolic_rate": [
                re.compile(rf"(?:basal\s*metabolic\s*rate|bmr){sep}{num}", re.IGNORECASE),
            ],
            "total_body_water": [
                re.compile(rf"(?:total\s*body\s*water|tbw){sep}{num}", re.IGNORECASE),
            ],
            "phase_angle": [
                re.compile(rf"(?:phase\s*angle|pa){sep}{num}\s*(?:°|deg)?", re.IGNORECASE),
            ],
            "ecw_tbw_ratio": [
                re.compile(rf"(?:ecw[\s/]tbw|extracellular[\s/]total\s*body\s*water){sep}{num}", re.IGNORECASE),
            ],
            "smi": [
                re.compile(rf"(?:smi|skeletal\s*muscle\s*index){sep}{num}", re.IGNORECASE),
            ],
        }

    def _build_cardiac_patterns(self) -> Dict[str, List[re.Pattern]]:
        num = r"([<>=]*\s*\d+\.?\d*)"
        sep = r"[^\d\n:]*[:\-=]?\s*"
        return {
            "systolic_bp": [
                re.compile(rf"(?:systolic|sbp|sys){sep}{num}", re.IGNORECASE),
                re.compile(rf"(?:bp|blood\s*pressure){sep}{num}\s*/", re.IGNORECASE),
            ],
            "diastolic_bp": [
                re.compile(rf"(?:diastolic|dbp|dia){sep}{num}", re.IGNORECASE),
                re.compile(rf"(?:bp|blood\s*pressure)\s*[:\-]?\s*\d+\s*/\s*{num}", re.IGNORECASE),
            ],
            "heart_rate": [
                re.compile(rf"(?:heart\s*rate|pulse|hr){sep}{num}", re.IGNORECASE),
            ],
            "ejection_fraction": [
                re.compile(rf"(?:ejection\s*fraction|ef|lvef){sep}{num}", re.IGNORECASE),
            ],
            "e_a_ratio": [
                re.compile(rf"(?:e/a|e[\s]*/[\s]*a)\s*(?:ratio)?{sep}{num}", re.IGNORECASE),
            ],
            "calcium_score": [
                re.compile(rf"(?:calcium\s*score|cac\s*score|coronary\s*calcium){sep}{num}", re.IGNORECASE),
            ],
            "diastolic_dysfunction": [
                re.compile(r"(?:diastolic\s*dysfunction)\s*[:\-]?\s*(?:grade\s*)?(none|i{1,3}|1|2|3|mild|moderate|severe|normal)", re.IGNORECASE),
            ],
        }

    # ─── TEXT EXTRACTION ──────────────────────────────────────────────

    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF using pdfplumber, with PyMuPDF fallback."""
        text = ""

        # Primary: pdfplumber
        try:
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                    # Also extract tables
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
        except Exception:
            pass

        # Fallback: PyMuPDF if pdfplumber yields little text
        if len(text.strip()) < 100:
            try:
                doc = fitz.open(filepath)
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            except Exception:
                pass

        return text

    # ─── PATTERN MATCHING ─────────────────────────────────────────────

    def _extract_values(self, text: str, patterns: Dict[str, List[re.Pattern]]) -> Dict[str, Any]:
        """Apply regex patterns to extract values from text."""
        extracted = {}
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = pattern.search(text)
                if match:
                    raw_val = match.group(1)
                    clean_val = raw_val.replace("<", "").replace(">", "").replace("=", "").strip()
                    try:
                        if "." in clean_val:
                            extracted[key] = float(clean_val)
                        else:
                            extracted[key] = int(clean_val)
                    except (ValueError, TypeError):
                        extracted[key] = raw_val
                    break
        return extracted

    def _extract_text_values(self, text: str, patterns: Dict[str, List[re.Pattern]]) -> Dict[str, Any]:
        """Extract text-based values (not just numeric)."""
        extracted = {}
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = pattern.search(text)
                if match:
                    extracted[key] = match.group(1).strip()
                    break
        return extracted

    # ─── MAIN EXTRACTION ─────────────────────────────────────────────

    def extract_text_from_excel(self, filepath: str) -> str:
        """Extract tabular data from an Excel file into a regex-friendly string format."""
        try:
            import pandas as pd
            # Find the actual header row
            df_raw = pd.read_excel(filepath, header=None, engine="calamine")
            header_idx = 0
            for i, row in df_raw.iterrows():
                row_str = " ".join([str(val).lower() for val in row.values])
                if "service name" in row_str or "result value" in row_str or "patient name" in row_str:
                    header_idx = i
                    break
            
            df = pd.read_excel(filepath, header=header_idx, engine="calamine")
            text = ""
            for _, row in df.iterrows():
                test_name = None
                for candidate in ["name to be printed", "parameter", "test name", "investigation", "service name"]:
                    for col in df.columns:
                        if candidate in str(col).lower():
                            test_name = str(row[col])
                            break
                    if test_name:
                        break
                
                result_val = None
                for candidate in ["result value", "result", "value"]:
                    for col in df.columns:
                        if candidate in str(col).lower():
                            result_val = str(row[col])
                            break
                    if result_val:
                        break
                
                if test_name is not None and str(test_name).lower() != "nan" and result_val is not None and str(result_val).lower() != "nan":
                    text += f"{test_name}: {result_val}\n"

            for _, row in df.iterrows():
                has_patient = False
                for col in df.columns:
                    col_str = str(col).lower()
                    if "patient name" in col_str and str(row[col]).lower() != "nan":
                        text += f"Patient Name: {row[col]}\n"
                        has_patient = True
                    if "age" in col_str and str(row[col]).lower() != "nan":
                        text += f"Age: {row[col]}\n"
                    if ("gender" in col_str or "sex" in col_str) and str(row[col]).lower() != "nan":
                        text += f"Gender: {row[col]}\n"
                if has_patient:
                    break
                    
            return text
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return ""

    def extract_from_files(
        self,
        laboratory_report_path: Optional[str] = None,
        radiology_report_path: Optional[str] = None,
        excel_report_path: Optional[str] = None,
    ) -> ExtractedPatientData:
        """
        Extract structured patient data from PDF and Excel files.
        Each file is parsed and values are merged into a unified schema.
        """
        all_text = ""

        for filepath in [laboratory_report_path, radiology_report_path]:
            if filepath is not None and Path(filepath).exists():
                all_text += self.extract_text_from_pdf(filepath) + "\n\n"
                
        if excel_report_path is not None and Path(excel_report_path).exists():
            all_text += self.extract_text_from_excel(excel_report_path) + "\n\n"

        if not all_text.strip():
            return ExtractedPatientData()

        # Extract patient info
        patient_vals = self._extract_text_values(all_text, self.patient_patterns)
        patient = PatientInfo(
            age=int(patient_vals["age"]) if "age" in patient_vals else None,
            gender=patient_vals.get("gender"),
            name=patient_vals.get("name"),
        )

        # Extract all lab values
        lab_vals = self._extract_values(all_text, self.lab_patterns)
        labs = LabValues(**{k: v for k, v in lab_vals.items() if hasattr(LabValues, k)})

        # Lipids
        lipid_vals = self._extract_values(all_text, self.lipid_patterns)
        lipids = LipidProfile(**{k: v for k, v in lipid_vals.items() if hasattr(LipidProfile, k)})

        # Liver
        liver_vals = {**self._extract_values(all_text, self.liver_patterns),
                      **self._extract_text_values(all_text, {"fatty_liver_grade": self.liver_patterns.get("fatty_liver_grade", [])})}
        liver = LiverPanel(**{k: v for k, v in liver_vals.items() if hasattr(LiverPanel, k)})

        # Inflammation
        infl_vals = self._extract_values(all_text, self.inflammation_patterns)
        inflammation = InflammationMarkers(**{k: v for k, v in infl_vals.items() if hasattr(InflammationMarkers, k)})

        # InBody
        inbody_vals = self._extract_values(all_text, self.inbody_patterns)
        inbody = InBodyMetrics(**{k: v for k, v in inbody_vals.items() if hasattr(InBodyMetrics, k)})

        # Cardiac
        cardiac_vals = self._extract_values(all_text, self.cardiac_patterns)
        # Also try to extract text-based findings
        echo_match = re.search(r"(?:echo(?:cardiograph?y?)?\s*(?:findings?|impression|report))\s*[:\-]?\s*(.+?)(?:\n|$)", all_text, re.IGNORECASE)
        ecg_match = re.search(r"(?:ecg|ekg|electrocardiogra(?:m|phy))\s*(?:findings?|impression|report)?\s*[:\-]?\s*(.+?)(?:\n|$)", all_text, re.IGNORECASE)
        if echo_match:
            cardiac_vals["echo_findings"] = echo_match.group(1).strip()
        if ecg_match:
            cardiac_vals["ecg_findings"] = ecg_match.group(1).strip()

        cardiac = CardiacFindings(**{k: v for k, v in cardiac_vals.items() if hasattr(CardiacFindings, k)})

        cardiac = CardiacFindings(**{k: v for k, v in cardiac_vals.items() if hasattr(CardiacFindings, k)})

        return ExtractedPatientData(
            patient=patient,
            labs=labs,
            lipids=lipids,
            liver=liver,
            inflammation=inflammation,
            inbody=inbody,
            cardiac=cardiac,
            raw_text=all_text
        )


# Singleton instance
pdf_extractor = PDFExtractor()
