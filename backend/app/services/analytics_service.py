from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy.orm import Session

from app.core.base_service import BaseService
from app.models.db_models import Dataset
from app.schemas.schemas import AnalyticsRequest, AnalyticsResult
from app.services.ingestion_service import IngestionService


class AnalyticsService(BaseService):
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def run_analytics(self, dataset: Dataset, request: AnalyticsRequest) -> AnalyticsResult:
        df = self.ingestion.load_dataframe(dataset)
        if df.empty or request.target_column not in df.columns:
            return AnalyticsResult(
                dataset_id=dataset.id,
                target_column=request.target_column,
                summary={},
            )

        result = AnalyticsResult(
            dataset_id=dataset.id,
            target_column=request.target_column,
            summary=self._summary_stats(df, request.target_column),
        )

        if "trend" in request.operations and request.date_column and request.date_column in df.columns:
            result.trends = self._trend_analysis(df, request.date_column, request.target_column)

        if "anomalies" in request.operations:
            result.anomalies = self._find_anomalies(df, request.target_column)

        if "kpis" in request.operations:
            result.kpis = self._compute_kpis(df, request.target_column, request.group_by)

        return result

    def _summary_stats(self, df: pd.DataFrame, col: str) -> Dict[str, Any]:
        series = df[col].dropna()
        if series.empty:
            return {}
        if series.dtype in [np.float64, np.int64]:
            return {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "std": round(float(series.std()), 4),
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "q25": round(float(series.quantile(0.25)), 4),
                "q75": round(float(series.quantile(0.75)), 4),
                "skewness": round(float(series.skew()), 4),
                "kurtosis": round(float(series.kurtosis()), 4),
            }
        return {
            "count": int(series.count()),
            "unique": int(series.nunique()),
            "top": str(series.mode()[0]) if not series.mode().empty else None,
            "freq": int(series.value_counts().iloc[0]) if not series.value_counts().empty else 0,
        }

    def _trend_analysis(self, df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
        try:
            df_sorted = df[[date_col, value_col]].copy()
            df_sorted[date_col] = pd.to_datetime(df_sorted[date_col], errors="coerce")
            df_sorted = df_sorted.dropna().sort_values(date_col)
            df_sorted["ma7"] = df_sorted[value_col].rolling(7, min_periods=1).mean()
            df_sorted["ma30"] = df_sorted[value_col].rolling(30, min_periods=1).mean()
            slope, _, r_value, _, _ = stats.linregress(
                range(len(df_sorted)), df_sorted[value_col].fillna(0)
            )
            return {
                "direction": "increasing" if slope > 0 else "decreasing",
                "slope": round(float(slope), 6),
                "r_squared": round(float(r_value ** 2), 4),
                "data_points": len(df_sorted),
                "moving_averages": df_sorted[[date_col, "ma7", "ma30"]]
                .tail(30)
                .assign(**{date_col: df_sorted[date_col].dt.strftime("%Y-%m-%d")})
                .to_dict(orient="records"),
            }
        except Exception as e:
            return {"error": str(e)}

    def _find_anomalies(self, df: pd.DataFrame, col: str) -> List[Dict[str, Any]]:
        if df[col].dtype not in [np.float64, np.int64]:
            return []
        series = df[col].dropna()
        if series.empty:
            return []
        z_scores = np.abs(stats.zscore(series))
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        anomalies = []
        for idx, (val, z) in enumerate(zip(series, z_scores)):
            is_zscore_outlier = z > 3
            is_iqr_outlier = val < (q1 - 1.5 * iqr) or val > (q3 + 1.5 * iqr)
            if is_zscore_outlier or is_iqr_outlier:
                anomalies.append({
                    "index": int(series.index[idx]),
                    "value": round(float(val), 4),
                    "z_score": round(float(z), 4),
                    "method": "z_score" if is_zscore_outlier else "iqr",
                })
        return anomalies[:50]

    def _compute_kpis(self, df: pd.DataFrame, col: str, group_by: Optional[List[str]]) -> Dict[str, Any]:
        if df[col].dtype not in [np.float64, np.int64]:
            return {}
        kpis: Dict[str, Any] = {
            "total": round(float(df[col].sum()), 4),
            "average": round(float(df[col].mean()), 4),
            "count": int(df[col].count()),
            "growth_rate": None,
        }
        if group_by:
            valid_groups = [g for g in group_by if g in df.columns]
            if valid_groups:
                grouped = df.groupby(valid_groups)[col].agg(["sum", "mean", "count"]).reset_index()
                kpis["by_group"] = grouped.to_dict(orient="records")
        return kpis

    def compute_kpis(self, dataset: Dataset) -> Dict[str, Any]:
        df = self.ingestion.load_dataframe(dataset)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        result = {}
        for col in numeric_cols[:10]:
            result[col] = self._compute_kpis(df, col, None)
        return result

    def detect_anomalies(self, dataset: Dataset, column: str) -> Dict[str, Any]:
        df = self.ingestion.load_dataframe(dataset)
        return {"column": column, "anomalies": self._find_anomalies(df, column)}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dataset = payload.get("dataset")
        request = payload.get("request")
        if dataset is None or request is None:
            return {"error": "dataset and request are required"}
        result = self.run_analytics(dataset, request)
        return result.model_dump()
