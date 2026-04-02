import io
import os
from typing import Any, Dict

import pandas as pd

from app.config import settings
from app.models.db_models import Dataset


class IngestionService:
    def __init__(self, db):
        self.db = db

    def ingest_file(self, content: bytes, filename: str, name: str, description: str = None) -> Dataset:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"
        file_path = os.path.join(settings.UPLOAD_DIR, f"{name.replace(' ', '_')}_{id(content)}.{ext}")

        with open(file_path, "wb") as f:
            f.write(content)

        df = self._read_file(content, ext)
        column_info = self._infer_column_info(df)

        dataset = Dataset(
            name=name,
            description=description,
            file_path=file_path,
            file_type=ext,
            row_count=len(df),
            column_count=len(df.columns),
            column_info=column_info,
            status="ready",
        )
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def _read_file(self, content: bytes, ext: str) -> pd.DataFrame:
        buf = io.BytesIO(content)
        if ext in ("xlsx", "xls"):
            return pd.read_excel(buf)
        return pd.read_csv(buf)

    def _infer_column_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        info = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            info[col] = {
                "dtype": dtype,
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().mean() * 100, 2),
                "unique_count": int(df[col].nunique()),
            }
            if df[col].dtype in ["int64", "float64"]:
                info[col].update({
                    "min": float(df[col].min()) if not df[col].isna().all() else None,
                    "max": float(df[col].max()) if not df[col].isna().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isna().all() else None,
                })
        return info

    def get_preview(self, dataset: Dataset, rows: int = 10) -> Dict[str, Any]:
        if not dataset.file_path or not os.path.exists(dataset.file_path):
            return {"columns": [], "data": [], "row_count": 0}
        ext = dataset.file_type or "csv"
        if ext in ("xlsx", "xls"):
            df = pd.read_excel(dataset.file_path, nrows=rows)
        else:
            df = pd.read_csv(dataset.file_path, nrows=rows)
        return {
            "columns": df.columns.tolist(),
            "data": df.head(rows).fillna("").to_dict(orient="records"),
            "row_count": dataset.row_count,
        }

    def load_dataframe(self, dataset: Dataset) -> pd.DataFrame:
        if not dataset.file_path or not os.path.exists(dataset.file_path):
            return pd.DataFrame()
        ext = dataset.file_type or "csv"
        if ext in ("xlsx", "xls"):
            return pd.read_excel(dataset.file_path)
        return pd.read_csv(dataset.file_path)
