from typing import Any, Dict, List

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.models.db_models import Dataset
from app.schemas.schemas import QualityScore
from app.services.ingestion_service import IngestionService


class QualityService(BaseService):
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def compute_quality(self, dataset: Dataset) -> QualityScore:
        df = self.ingestion.load_dataframe(dataset)
        if df.empty:
            return QualityScore(
                overall_score=0.0,
                completeness=0.0,
                consistency=0.0,
                validity=0.0,
                uniqueness=0.0,
                column_profiles={},
                issues=[],
            )

        completeness = self._completeness(df)
        consistency = self._consistency(df)
        validity = self._validity(df)
        uniqueness = self._uniqueness(df)

        overall = round((completeness + consistency + validity + uniqueness) / 4, 2)

        dataset.quality_score = overall
        self.db.commit()

        return QualityScore(
            overall_score=overall,
            completeness=completeness,
            consistency=consistency,
            validity=validity,
            uniqueness=uniqueness,
            column_profiles=self._column_profiles(df),
            issues=self._detect_issues(df),
        )

    def _completeness(self, df: pd.DataFrame) -> float:
        total_cells = df.size
        if total_cells == 0:
            return 100.0
        missing = df.isna().sum().sum()
        return round((1 - missing / total_cells) * 100, 2)

    def _consistency(self, df: pd.DataFrame) -> float:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.empty:
            return 100.0
        anomaly_cols = 0
        for col in numeric.columns:
            z = np.abs(stats.zscore(numeric[col].dropna()))
            if (z > 3).sum() > 0:
                anomaly_cols += 1
        score = max(0, 100 - (anomaly_cols / len(numeric.columns)) * 100)
        return round(score, 2)

    def _validity(self, df: pd.DataFrame) -> float:
        issues = 0
        total_checks = 0
        for col in df.columns:
            total_checks += 1
            if df[col].dtype == object:
                mixed = df[col].dropna().apply(lambda x: isinstance(x, (int, float))).mean()
                if mixed > 0.1:
                    issues += 1
        if total_checks == 0:
            return 100.0
        return round((1 - issues / total_checks) * 100, 2)

    def _uniqueness(self, df: pd.DataFrame) -> float:
        if len(df) == 0:
            return 100.0
        dups = df.duplicated().sum()
        return round((1 - dups / len(df)) * 100, 2)

    def _column_profiles(self, df: pd.DataFrame) -> Dict[str, Any]:
        profiles = {}
        for col in df.columns:
            profile: Dict[str, Any] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().mean() * 100, 2),
                "unique_count": int(df[col].nunique()),
                "unique_pct": round(df[col].nunique() / max(len(df), 1) * 100, 2),
            }
            if df[col].dtype in [np.float64, np.int64]:
                non_null = df[col].dropna()
                if not non_null.empty:
                    profile.update({
                        "min": round(float(non_null.min()), 4),
                        "max": round(float(non_null.max()), 4),
                        "mean": round(float(non_null.mean()), 4),
                        "median": round(float(non_null.median()), 4),
                        "std": round(float(non_null.std()), 4),
                    })
            elif df[col].dtype == object:
                top_vals = df[col].value_counts().head(5).to_dict()
                profile["top_values"] = {str(k): int(v) for k, v in top_vals.items()}
            profiles[col] = profile
        return profiles

    def _detect_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        issues = []
        for col in df.columns:
            null_pct = df[col].isna().mean() * 100
            if null_pct > 50:
                issues.append({"column": col, "issue": "high_missing", "severity": "critical", "detail": f"{null_pct:.1f}% missing"})
            elif null_pct > 20:
                issues.append({"column": col, "issue": "moderate_missing", "severity": "warning", "detail": f"{null_pct:.1f}% missing"})

            if df[col].dtype in [np.float64, np.int64]:
                non_null = df[col].dropna()
                if not non_null.empty:
                    z = np.abs(stats.zscore(non_null))
                    outlier_pct = (z > 3).mean() * 100
                    if outlier_pct > 5:
                        issues.append({"column": col, "issue": "outliers", "severity": "warning", "detail": f"{outlier_pct:.1f}% outliers"})
        return issues

    def column_profile(self, dataset: Dataset) -> Dict[str, Any]:
        df = self.ingestion.load_dataframe(dataset)
        return self._column_profiles(df)

    def detect_drift(self, current: Dataset, reference: Dataset) -> Dict[str, Any]:
        df_curr = self.ingestion.load_dataframe(current)
        df_ref = self.ingestion.load_dataframe(reference)
        drift_results = {}
        common_cols = set(df_curr.columns) & set(df_ref.columns)
        for col in common_cols:
            if df_curr[col].dtype in [np.float64, np.int64]:
                curr_clean = df_curr[col].dropna()
                ref_clean = df_ref[col].dropna()
                if len(curr_clean) > 1 and len(ref_clean) > 1:
                    stat, pval = stats.ks_2samp(curr_clean, ref_clean)
                    drift_results[col] = {
                        "test": "ks_2samp",
                        "statistic": round(float(stat), 4),
                        "p_value": round(float(pval), 4),
                        "drift_detected": pval < 0.05,
                    }
        return {"drift_results": drift_results, "columns_checked": len(drift_results)}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dataset = payload.get("dataset")
        if dataset is None:
            return {"error": "dataset is required"}
        quality = self.compute_quality(dataset)
        return quality.model_dump()
