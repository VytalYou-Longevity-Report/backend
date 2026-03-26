"""
VYTALYOU™ Stage 4: Risk Projection Engine
Generates mortality and morbidity risk curves based on patient biomarkers.
"""

import math
from typing import List, Optional

from models.schemas import (
    ExtractedPatientData, DerivedMetrics,
    RiskProjection, RiskDataPoint,
)


class RiskEngine:
    """
    Computes 10-year mortality and morbidity risk projections
    using a multi-factor risk model based on:
    - Age
    - HbA1c / Glycemic control
    - hs-CRP / Inflammation
    - Visceral Fat Area
    - Liver steatosis
    - Sarcopenia
    - Cardiovascular markers
    """

    def compute_projections(
        self,
        data: ExtractedPatientData,
        metrics: DerivedMetrics,
        years: int = 10,
    ) -> RiskProjection:
        """Generate mortality and morbidity risk curves."""

        # Compute base risk factors (0-1 scale)
        age = data.patient.age or 50
        base_mortality = self._age_based_mortality(age)
        base_morbidity = self._age_based_morbidity(age)

        # Risk modifiers from biomarkers
        glycemic_risk = self._glycemic_risk(data, metrics)
        inflammation_risk = self._inflammation_risk(data)
        visceral_risk = self._visceral_risk(data)
        liver_risk = self._liver_risk(data)
        sarcopenia_risk = self._sarcopenia_risk(metrics)
        cardiac_risk = self._cardiac_risk(data)
        lipid_risk = self._lipid_risk(data, metrics)
        renal_risk = self._renal_risk(data)

        # Composite risk multiplier
        risk_multiplier = 1.0
        risk_multiplier *= (1 + glycemic_risk * 0.3)
        risk_multiplier *= (1 + inflammation_risk * 0.25)
        risk_multiplier *= (1 + visceral_risk * 0.2)
        risk_multiplier *= (1 + liver_risk * 0.15)
        risk_multiplier *= (1 + sarcopenia_risk * 0.2)
        risk_multiplier *= (1 + cardiac_risk * 0.25)
        risk_multiplier *= (1 + lipid_risk * 0.15)
        risk_multiplier *= (1 + renal_risk * 0.15)

        # Morbidity multiplier is typically higher as morbidity precedes mortality
        morbidity_multiplier = risk_multiplier * 1.3

        # Generate curves
        mortality_curve = []
        morbidity_curve = []
        baseline_mortality = []
        baseline_morbidity = []

        for year in range(0, years + 1):
            age_at_year = age + year

            # Baseline (population average)
            bm = self._cumulative_risk(base_mortality, year, age_at_year, 1.0)
            bmb = self._cumulative_risk(base_morbidity, year, age_at_year, 1.0)

            # Patient-specific
            pm = self._cumulative_risk(base_mortality, year, age_at_year, risk_multiplier)
            pmb = self._cumulative_risk(base_morbidity, year, age_at_year, morbidity_multiplier)

            mortality_curve.append(RiskDataPoint(year=year, risk_index=round(pm, 3)))
            morbidity_curve.append(RiskDataPoint(year=year, risk_index=round(pmb, 3)))
            baseline_mortality.append(RiskDataPoint(year=year, risk_index=round(bm, 3)))
            baseline_morbidity.append(RiskDataPoint(year=year, risk_index=round(bmb, 3)))

        return RiskProjection(
            mortality_curve=mortality_curve,
            morbidity_curve=morbidity_curve,
            baseline_mortality=baseline_mortality,
            baseline_morbidity=baseline_morbidity,
        )

    # ─── BASE RISK FUNCTIONS ─────────────────────────────────────────

    @staticmethod
    def _age_based_mortality(age: int) -> float:
        """Annual mortality rate by age (simplified Gompertz)."""
        # Gompertz: µ(x) = a * exp(b * x)
        a = 0.00001
        b = 0.085
        return a * math.exp(b * age)

    @staticmethod
    def _age_based_morbidity(age: int) -> float:
        """Annual morbidity rate by age."""
        a = 0.0001
        b = 0.065
        return a * math.exp(b * age)

    @staticmethod
    def _cumulative_risk(
        annual_rate: float, years: int, current_age: int, multiplier: float
    ) -> float:
        """Compute cumulative risk over N years."""
        survival = 1.0
        for y in range(years):
            age = current_age + y
            # Age-adjusted annual rate
            a_mort = 0.00001 * math.exp(0.085 * age) * multiplier
            survival *= (1 - min(a_mort, 0.99))
        return round(min(1 - survival, 1.0), 4)

    # ─── RISK FACTOR COMPUTATIONS ────────────────────────────────────

    @staticmethod
    def _glycemic_risk(data: ExtractedPatientData, metrics: DerivedMetrics) -> float:
        """0-1 glycemic risk score."""
        score = 0.0
        if data.labs.hba1c is not None:
            if data.labs.hba1c >= 8.0:
                score += 0.5
            elif data.labs.hba1c >= 6.5:
                score += 0.3
            elif data.labs.hba1c >= 5.7:
                score += 0.15
        if metrics.homa_ir is not None:
            if metrics.homa_ir > 3.0:
                score += 0.3
            elif metrics.homa_ir > 2.0:
                score += 0.15
        if data.labs.fasting_glucose is not None and data.labs.fasting_glucose > 126:
            score += 0.2
        return min(score, 1.0)

    @staticmethod
    def _inflammation_risk(data: ExtractedPatientData) -> float:
        score = 0.0
        if data.inflammation.hs_crp is not None:
            if data.inflammation.hs_crp > 3.0:
                score += 0.4
            elif data.inflammation.hs_crp > 1.0:
                score += 0.2
        if data.inflammation.homocysteine is not None:
            if data.inflammation.homocysteine > 15:
                score += 0.3
            elif data.inflammation.homocysteine > 10:
                score += 0.15
        if data.inflammation.il6 is not None and data.inflammation.il6 > 3:
            score += 0.3
        return min(score, 1.0)

    @staticmethod
    def _visceral_risk(data: ExtractedPatientData) -> float:
        if data.inbody.visceral_fat_area is not None:
            vfa = data.inbody.visceral_fat_area
            if vfa > 160:
                return 0.8
            elif vfa > 130:
                return 0.5
            elif vfa > 100:
                return 0.3
            else:
                return 0.0
        return 0.0

    @staticmethod
    def _liver_risk(data: ExtractedPatientData) -> float:
        score = 0.0
        if data.liver.fatty_liver_grade is not None:
            grade = data.liver.fatty_liver_grade.lower()
            if grade in ("iii", "3", "severe"):
                score += 0.5
            elif grade in ("ii", "2", "moderate"):
                score += 0.3
            elif grade in ("i", "1", "mild"):
                score += 0.15
        if data.liver.sgpt_alt is not None and data.liver.sgpt_alt > 60:
            score += 0.2
        if data.liver.fibroscan_kpa is not None and data.liver.fibroscan_kpa > 9.5:
            score += 0.3
        return min(score, 1.0)

    @staticmethod
    def _sarcopenia_risk(metrics: DerivedMetrics) -> float:
        if metrics.sarcopenia_risk is not None:
            from models.schemas import RiskCategory
            mapping = {
                RiskCategory.LOW: 0.0,
                RiskCategory.MODERATE: 0.2,
                RiskCategory.HIGH: 0.5,
                RiskCategory.VERY_HIGH: 0.8,
            }
            return mapping.get(metrics.sarcopenia_risk, 0.0)
        return 0.0

    @staticmethod
    def _cardiac_risk(data: ExtractedPatientData) -> float:
        score = 0.0
        if data.cardiac.systolic_bp is not None:
            if data.cardiac.systolic_bp >= 160:
                score += 0.4
            elif data.cardiac.systolic_bp >= 140:
                score += 0.25
            elif data.cardiac.systolic_bp >= 130:
                score += 0.1
        if data.cardiac.calcium_score is not None:
            if data.cardiac.calcium_score > 400:
                score += 0.4
            elif data.cardiac.calcium_score > 100:
                score += 0.25
            elif data.cardiac.calcium_score > 0:
                score += 0.1
        if data.cardiac.ejection_fraction is not None and data.cardiac.ejection_fraction < 50:
            score += 0.3
        return min(score, 1.0)

    @staticmethod
    def _lipid_risk(data: ExtractedPatientData, metrics: DerivedMetrics) -> float:
        score = 0.0
        if data.lipids.ldl is not None:
            if data.lipids.ldl > 190:
                score += 0.4
            elif data.lipids.ldl > 130:
                score += 0.2
        if metrics.tg_hdl_ratio is not None:
            if metrics.tg_hdl_ratio > 5:
                score += 0.3
            elif metrics.tg_hdl_ratio > 3.5:
                score += 0.15
        if data.lipids.apob is not None and data.lipids.apob > 120:
            score += 0.2
        return min(score, 1.0)

    @staticmethod
    def _renal_risk(data: ExtractedPatientData) -> float:
        score = 0.0
        if data.labs.egfr is not None:
            if data.labs.egfr < 30:
                score += 0.6
            elif data.labs.egfr < 60:
                score += 0.3
            elif data.labs.egfr < 90:
                score += 0.1
        if data.labs.creatinine is not None:
            if data.labs.creatinine > 2.0:
                score += 0.3
            elif data.labs.creatinine > 1.3:
                score += 0.1
        return min(score, 1.0)


# Singleton
risk_engine = RiskEngine()
