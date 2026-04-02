from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import Dataset
from app.schemas.schemas import NLQRequest, NLQResponse
from app.services.ingestion_service import IngestionService


class NLQService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def process_query(self, request: NLQRequest) -> NLQResponse:
        query = request.query.lower().strip()
        df: Optional[pd.DataFrame] = None

        if request.dataset_id:
            dataset = self.db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
            if dataset:
                df = self.ingestion.load_dataframe(dataset)

        interpretation, result, explanation = self._interpret(query, df)

        return NLQResponse(
            query=request.query,
            interpretation=interpretation,
            result=result,
            explanation=explanation,
        )

    def _interpret(self, query: str, df: Optional[pd.DataFrame]):        # Average / mean
        if any(w in query for w in ["average", "mean", "avg"]):
            col = self._find_column(query, df)
            if col and df is not None and col in df.columns:
                val = df[col].mean()
                return (
                    f"compute average of '{col}'",
                    {"column": col, "average": round(float(val), 4)},
                    f"The average of '{col}' is {val:.4f}",
                )

        # Sum / total
        if any(w in query for w in ["sum", "total"]):
            col = self._find_column(query, df)
            if col and df is not None and col in df.columns:
                val = df[col].sum()
                return (
                    f"compute sum of '{col}'",
                    {"column": col, "sum": round(float(val), 4)},
                    f"The sum of '{col}' is {val:.4f}",
                )

        # Count / rows
        if any(w in query for w in ["count", "how many", "rows", "records"]):
            if df is not None:
                return (
                    "count rows",
                    {"row_count": len(df)},
                    f"The dataset has {len(df)} rows",
                )

        # Max
        if "max" in query or "maximum" in query or "highest" in query:
            col = self._find_column(query, df)
            if col and df is not None and col in df.columns:
                val = df[col].max()
                return (
                    f"find maximum of '{col}'",
                    {"column": col, "max": round(float(val), 4)},
                    f"The maximum value of '{col}' is {val:.4f}",
                )

        # Min
        if "min" in query or "minimum" in query or "lowest" in query:
            col = self._find_column(query, df)
            if col and df is not None and col in df.columns:
                val = df[col].min()
                return (
                    f"find minimum of '{col}'",
                    {"column": col, "min": round(float(val), 4)},
                    f"The minimum value of '{col}' is {val:.4f}",
                )

        # Columns
        if any(w in query for w in ["columns", "fields", "features"]):
            cols = df.columns.tolist() if df is not None else []
            return (
                "list columns",
                {"columns": cols, "count": len(cols)},
                f"The dataset has {len(cols)} columns: {', '.join(cols[:10])}{'...' if len(cols) > 10 else ''}",
            )

        return (
            "general query",
            None,
            "I couldn't interpret that query. Try asking for sum, average, max, min, or count of a specific column.",
        )

    def _find_column(self, query: str, df: Optional[pd.DataFrame]) -> Optional[str]:
        if df is None:
            return None
        for col in df.columns:
            if col.lower() in query:
                return col
        words = query.split()
        for col in df.columns:
            col_parts = col.lower().replace("_", " ").split()
            if any(part in words for part in col_parts):
                return col
        return None
