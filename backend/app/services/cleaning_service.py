from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import CleaningLog, Dataset
from app.schemas.schemas import CleaningRequest, CleaningResult
from app.services.ingestion_service import IngestionService


class CleaningService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def run_cleaning(self, dataset: Dataset, request: CleaningRequest) -> CleaningResult:
        df = self.ingestion.load_dataframe(dataset)
        if df.empty:
            return CleaningResult(
                dataset_id=dataset.id,
                operations_performed=[],
                rows_before=0,
                rows_after=0,
                columns_modified=[],
                report={},
            )

        rows_before = len(df)
        report: Dict[str, Any] = {}
        columns_modified: List[str] = []
        operations_performed: List[str] = []

        for op in request.operations:
            if op == "missing_values":
                df, op_report, cols = self._handle_missing(df, request.strategy)
                report["missing_values"] = op_report
                columns_modified.extend(cols)
                operations_performed.append("missing_values")
                self._log(dataset.id, "missing_values", op_report, len(cols))

            elif op == "duplicates":
                df, op_report = self._remove_duplicates(df)
                report["duplicates"] = op_report
                operations_performed.append("duplicates")
                self._log(dataset.id, "duplicates", op_report, op_report.get("removed", 0))

            elif op == "outliers":
                df, op_report, cols = self._handle_outliers(df)
                report["outliers"] = op_report
                columns_modified.extend(cols)
                operations_performed.append("outliers")
                self._log(dataset.id, "outliers", op_report, len(cols))

            elif op == "standardize":
                df, op_report, cols = self._standardize_categories(df)
                report["standardize"] = op_report
                columns_modified.extend(cols)
                operations_performed.append("standardize")
                self._log(dataset.id, "standardize", op_report, len(cols))

        # Persist cleaned file
        import os
        cleaned_path = dataset.file_path.replace(f".{dataset.file_type}", f"_cleaned.{dataset.file_type}")
        if dataset.file_type in ("xlsx", "xls"):
            df.to_excel(cleaned_path, index=False)
        else:
            df.to_csv(cleaned_path, index=False)

        dataset.file_path = cleaned_path
        dataset.row_count = len(df)
        self.db.commit()

        return CleaningResult(
            dataset_id=dataset.id,
            operations_performed=list(set(operations_performed)),
            rows_before=rows_before,
            rows_after=len(df),
            columns_modified=list(set(columns_modified)),
            report=report,
        )

    def _handle_missing(self, df: pd.DataFrame, strategy: str):
        report = {}
        modified_cols = []
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count == 0:
                continue
            report[col] = {"null_count": int(null_count)}
            if df[col].dtype in [np.float64, np.int64]:
                fill_val = df[col].median() if strategy == "median" else df[col].mean()
                df[col] = df[col].fillna(fill_val)
                report[col]["fill_method"] = "median" if strategy == "median" else "mean"
                report[col]["fill_value"] = round(float(fill_val), 4) if not np.isnan(fill_val) else 0
            else:
                mode = df[col].mode()
                fill_val = mode[0] if not mode.empty else "unknown"
                df[col] = df[col].fillna(fill_val)
                report[col]["fill_method"] = "mode"
                report[col]["fill_value"] = str(fill_val)
            modified_cols.append(col)
        return df, report, modified_cols

    def _remove_duplicates(self, df: pd.DataFrame):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        report = {"before": before, "after": len(df), "removed": removed}
        return df, report

    def _handle_outliers(self, df: pd.DataFrame):
        report = {}
        modified_cols = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            if outliers > 0:
                df[col] = df[col].clip(lower=lower, upper=upper)
                report[col] = {
                    "outliers_clipped": int(outliers),
                    "lower_bound": round(float(lower), 4),
                    "upper_bound": round(float(upper), 4),
                }
                modified_cols.append(col)
        return df, report, modified_cols

    def _standardize_categories(self, df: pd.DataFrame):
        report = {}
        modified_cols = []
        cat_cols = df.select_dtypes(include=["object"]).columns
        for col in cat_cols:
            original = df[col].copy()
            df[col] = df[col].str.strip().str.lower()
            changed = (original != df[col]).sum()
            if changed > 0:
                report[col] = {"values_standardized": int(changed)}
                modified_cols.append(col)
        return df, report, modified_cols

    def _log(self, dataset_id: int, operation: str, details: Dict, rows_affected: int):
        log = CleaningLog(
            dataset_id=dataset_id,
            operation=operation,
            details=details,
            rows_affected=rows_affected,
        )
        self.db.add(log)
        self.db.commit()
