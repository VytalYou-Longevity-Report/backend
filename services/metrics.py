"""
VYTALYOU™ Stage 2: Derived Longevity Metrics Calculator
Computes advanced biomarkers and risk scores from extracted patient data.
"""

import math
from typing import Optional

from models.schemas import (
    ExtractedPatientData, DerivedMetrics, RiskCategory,
)


class MetricsCalculator:
    """Computes derived longevity metrics from raw lab/body composition data."""

    def compute(self, data: ExtractedPatientData) -> DerivedMetrics:
        metrics = DerivedMetrics()

        # ─── HOMA-IR ─────────────────────────────────────────────────
        if data.labs.fasting_insulin is not None and data.labs.fasting_glucose is not None:
            metrics.homa_ir = round(
                (data.labs.fasting_insulin * data.labs.fasting_glucose) / 405, 2
            )
            metrics.homa_ir_risk = self._classify_homa_ir(metrics.homa_ir)

        # ─── TG/HDL Ratio ────────────────────────────────────────────
        if data.lipids.triglycerides is not None and data.lipids.hdl is not None and data.lipids.hdl > 0:
            metrics.tg_hdl_ratio = round(data.lipids.triglycerides / data.lipids.hdl, 2)
            metrics.tg_hdl_risk = self._classify_tg_hdl(metrics.tg_hdl_ratio)

        # ─── TyG Index ───────────────────────────────────────────────
        if data.lipids.triglycerides is not None and data.labs.fasting_glucose is not None:
            try:
                tg = data.lipids.triglycerides
                fbs = data.labs.fasting_glucose
                if tg > 0 and fbs > 0:
                    # TyG = ln(TG[mg/dL] × FBS[mg/dL] / 2)
                    metrics.tyg_index = round(math.log(tg * fbs / 2), 2)
                    metrics.tyg_risk = self._classify_tyg(metrics.tyg_index)
            except (ValueError, ZeroDivisionError):
                pass

        # ─── Visceral Fat Risk ────────────────────────────────────────
        if data.inbody.visceral_fat_area is not None:
            metrics.visceral_fat_risk = self._classify_visceral_fat(data.inbody.visceral_fat_area)
        elif data.inbody.visceral_fat_level is not None:
            metrics.visceral_fat_risk = self._classify_visceral_fat_level(data.inbody.visceral_fat_level)

        # ─── Sarcopenia Index ────────────────────────────────────────
        smi = data.inbody.smi
        if smi is None and data.inbody.skeletal_muscle_mass is not None and data.inbody.height is not None:
            height_m = data.inbody.height / 100
            if height_m > 0:
                smi = round(data.inbody.skeletal_muscle_mass / (height_m ** 2), 2)

        if smi is not None:
            metrics.sarcopenia_index = smi
            gender = (data.patient.gender or "").lower()
            metrics.sarcopenia_risk = self._classify_sarcopenia(smi, gender)

        # ─── Inflammation Composite ──────────────────────────────────
        metrics.inflammation_composite = self._compute_inflammation_score(data)

        # ─── Metabolic Syndrome Score ────────────────────────────────
        metrics.metabolic_syndrome_score = self._compute_mets_score(data)

        # ─── Biological Age Drift ────────────────────────────────────
        if data.patient.age is not None:
            bio_age = self._estimate_biological_age(data, metrics)
            metrics.estimated_biological_age = round(bio_age, 1)
            metrics.biological_age_drift = round(bio_age - data.patient.age, 1)

        return metrics

    # ─── CLASSIFIERS ─────────────────────────────────────────────────

    @staticmethod
    def _classify_homa_ir(value: float) -> RiskCategory:
        if value < 1.0:
            return RiskCategory.LOW
        elif value < 2.0:
            return RiskCategory.MODERATE
        elif value < 3.0:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    @staticmethod
    def _classify_tg_hdl(value: float) -> RiskCategory:
        if value < 2.0:
            return RiskCategory.LOW
        elif value < 3.5:
            return RiskCategory.MODERATE
        elif value < 5.0:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    @staticmethod
    def _classify_tyg(value: float) -> RiskCategory:
        if value < 8.0:
            return RiskCategory.LOW
        elif value < 8.5:
            return RiskCategory.MODERATE
        elif value < 9.0:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    @staticmethod
    def _classify_visceral_fat(vfa: float) -> RiskCategory:
        if vfa < 100:
            return RiskCategory.LOW
        elif vfa < 130:
            return RiskCategory.MODERATE
        elif vfa < 160:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    @staticmethod
    def _classify_visceral_fat_level(vfl: float) -> RiskCategory:
        if vfl <= 9:
            return RiskCategory.LOW
        elif vfl <= 14:
            return RiskCategory.MODERATE
        elif vfl <= 19:
            return RiskCategory.HIGH
        else:
            return RiskCategory.VERY_HIGH

    @staticmethod
    def _classify_sarcopenia(smi: float, gender: str) -> RiskCategory:
        # Cutoffs based on EWGSOP2 criteria
        if gender in ("female", "f"):
            if smi >= 6.0:
                return RiskCategory.LOW
            elif smi >= 5.5:
                return RiskCategory.MODERATE
            elif smi >= 5.0:
                return RiskCategory.HIGH
            else:
                return RiskCategory.VERY_HIGH
        else:  # Male or unspecified
            if smi >= 7.0:
                return RiskCategory.LOW
            elif smi >= 6.5:
                return RiskCategory.MODERATE
            elif smi >= 6.0:
                return RiskCategory.HIGH
            else:
                return RiskCategory.VERY_HIGH

    # ─── COMPOSITE SCORES ────────────────────────────────────────────

    def _compute_inflammation_score(self, data: ExtractedPatientData) -> Optional[float]:
        """Composite inflammation score (0-100) based on available markers."""
        scores = []
        weights = []

        if data.inflammation.hs_crp is not None:
            # hs-CRP: <1 optimal, 1-3 moderate, >3 high
            s = min(data.inflammation.hs_crp / 3.0 * 50, 100)
            scores.append(s)
            weights.append(3)
        elif data.inflammation.crp is not None:
            s = min(data.inflammation.crp / 10.0 * 50, 100)
            scores.append(s)
            weights.append(2)

        if data.inflammation.esr is not None:
            s = min(data.inflammation.esr / 30.0 * 50, 100)
            scores.append(s)
            weights.append(1)

        if data.inflammation.homocysteine is not None:
            # <10 optimal, >15 high
            s = min((data.inflammation.homocysteine - 5) / 10.0 * 50, 100)
            scores.append(max(s, 0))
            weights.append(2)

        if data.inflammation.il6 is not None:
            s = min(data.inflammation.il6 / 5.0 * 50, 100)
            scores.append(s)
            weights.append(2)

        if not scores:
            return None

        weighted = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        return round(weighted / total_weight, 1)

    def _compute_mets_score(self, data: ExtractedPatientData) -> Optional[int]:
        """Count metabolic syndrome criteria met (0-5)."""
        count = 0

        # 1. Elevated waist circumference (using VFA as proxy)
        if data.inbody.visceral_fat_area is not None and data.inbody.visceral_fat_area >= 100:
            count += 1
        elif data.inbody.bmi is not None and data.inbody.bmi >= 30:
            count += 1

        # 2. Elevated triglycerides >= 150
        if data.lipids.triglycerides is not None and data.lipids.triglycerides >= 150:
            count += 1

        # 3. Reduced HDL (<40 male, <50 female)
        if data.lipids.hdl is not None:
            gender = (data.patient.gender or "").lower()
            threshold = 50 if gender in ("female", "f") else 40
            if data.lipids.hdl < threshold:
                count += 1

        # 4. Elevated blood pressure >= 130/85
        if data.cardiac.systolic_bp is not None and data.cardiac.systolic_bp >= 130:
            count += 1
        elif data.cardiac.diastolic_bp is not None and data.cardiac.diastolic_bp >= 85:
            count += 1

        # 5. Elevated fasting glucose >= 100
        if data.labs.fasting_glucose is not None and data.labs.fasting_glucose >= 100:
            count += 1

        return count

    # ─── BIOLOGICAL AGE ESTIMATION ───────────────────────────────────

    def _estimate_biological_age(
        self, data: ExtractedPatientData, metrics: DerivedMetrics
    ) -> float:
        """
        Rule-based biological age estimation.
        Starts from chronological age and applies drift based on biomarkers.
        """
        chrono_age = data.patient.age
        drift = 0.0

        # HbA1c drift
        if data.labs.hba1c is not None:
            if data.labs.hba1c > 6.5:
                drift += (data.labs.hba1c - 5.7) * 2.0
            elif data.labs.hba1c > 5.7:
                drift += (data.labs.hba1c - 5.7) * 1.0
            elif data.labs.hba1c < 5.2:
                drift -= 1.0

        # Insulin resistance drift
        if metrics.homa_ir is not None:
            if metrics.homa_ir > 3.0:
                drift += 3.0
            elif metrics.homa_ir > 2.0:
                drift += 1.5
            elif metrics.homa_ir < 1.0:
                drift -= 1.0

        # Inflammation drift
        if data.inflammation.hs_crp is not None:
            if data.inflammation.hs_crp > 3.0:
                drift += 3.0
            elif data.inflammation.hs_crp > 1.0:
                drift += 1.0
            elif data.inflammation.hs_crp < 0.5:
                drift -= 1.0

        # Lipid drift
        if metrics.tg_hdl_ratio is not None:
            if metrics.tg_hdl_ratio > 5:
                drift += 2.0
            elif metrics.tg_hdl_ratio > 3.5:
                drift += 1.0
            elif metrics.tg_hdl_ratio < 2.0:
                drift -= 0.5

        # Body composition drift
        if data.inbody.visceral_fat_area is not None:
            if data.inbody.visceral_fat_area > 160:
                drift += 3.0
            elif data.inbody.visceral_fat_area > 100:
                drift += 1.5
            elif data.inbody.visceral_fat_area < 80:
                drift -= 1.0

        # Sarcopenia drift
        if metrics.sarcopenia_risk is not None:
            if metrics.sarcopenia_risk == RiskCategory.VERY_HIGH:
                drift += 4.0
            elif metrics.sarcopenia_risk == RiskCategory.HIGH:
                drift += 2.0
            elif metrics.sarcopenia_risk == RiskCategory.LOW:
                drift -= 1.0

        # Phase angle (cellular health)
        if data.inbody.phase_angle is not None:
            if data.inbody.phase_angle > 6.0:
                drift -= 2.0
            elif data.inbody.phase_angle < 4.5:
                drift += 2.0

        # Liver health
        if data.liver.sgpt_alt is not None and data.liver.sgpt_alt > 40:
            drift += 1.0
        if data.liver.fatty_liver_grade is not None:
            grade = data.liver.fatty_liver_grade.lower()
            if grade in ("iii", "3", "severe"):
                drift += 3.0
            elif grade in ("ii", "2", "moderate"):
                drift += 1.5
            elif grade in ("i", "1", "mild"):
                drift += 0.5

        # Kidney function
        if data.labs.egfr is not None:
            if data.labs.egfr < 60:
                drift += 3.0
            elif data.labs.egfr < 90:
                drift += 1.0
            elif data.labs.egfr > 100:
                drift -= 0.5

        return chrono_age + drift


# Singleton
metrics_calculator = MetricsCalculator()
