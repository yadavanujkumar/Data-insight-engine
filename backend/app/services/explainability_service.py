from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session

from app.services.ingestion_service import IngestionService


class ExplainabilityService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def feature_importance(self, df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
        if target_col not in df.columns:
            return {"error": f"Target column '{target_col}' not found"}

        df_clean = df.dropna()
        if len(df_clean) < 10:
            return {"error": "Not enough data for feature importance analysis"}

        feature_cols = [c for c in df_clean.columns if c != target_col]
        X = pd.DataFrame()

        for col in feature_cols:
            if df_clean[col].dtype in [np.float64, np.int64]:
                X[col] = df_clean[col]
            elif df_clean[col].dtype == object:
                le = LabelEncoder()
                X[col] = le.fit_transform(df_clean[col].astype(str))

        if X.empty:
            return {"error": "No usable feature columns"}

        y = df_clean[target_col]
        is_classification = y.nunique() <= 20 and y.dtype == object

        try:
            if is_classification:
                le = LabelEncoder()
                y_enc = le.fit_transform(y.astype(str))
                model = RandomForestClassifier(n_estimators=50, random_state=42)
                model.fit(X, y_enc)
            else:
                model = RandomForestRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)

            importances = dict(zip(X.columns, model.feature_importances_))
            sorted_imp = sorted(importances.items(), key=lambda x: x[1], reverse=True)

            return {
                "target_column": target_col,
                "model_type": "random_forest_classifier" if is_classification else "random_forest_regressor",
                "feature_importances": [
                    {"feature": k, "importance": round(float(v), 4)}
                    for k, v in sorted_imp
                ],
                "top_feature": sorted_imp[0][0] if sorted_imp else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_explanation(self, result: Dict[str, Any]) -> str:
        if "error" in result:
            return f"Could not generate explanation: {result['error']}"

        top = result.get("feature_importances", [])
        if not top:
            return "No feature importance data available."

        lines = [f"Model: {result.get('model_type', 'unknown')}"]
        lines.append(f"Top features for predicting '{result.get('target_column')}':")
        for item in top[:5]:
            pct = item["importance"] * 100
            lines.append(f"  - {item['feature']}: {pct:.1f}% importance")
        return "\n".join(lines)
