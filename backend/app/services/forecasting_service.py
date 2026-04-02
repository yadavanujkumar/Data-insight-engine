from typing import Dict

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, Prediction
from app.schemas.schemas import ForecastRequest, ForecastResult
from app.services.ingestion_service import IngestionService


class ForecastingService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def forecast(self, dataset: Dataset, request: ForecastRequest) -> ForecastResult:
        df = self.ingestion.load_dataframe(dataset)

        if df.empty or request.target_column not in df.columns:
            return ForecastResult(
                dataset_id=dataset.id,
                target_column=request.target_column,
                horizon=request.horizon,
                predictions=[],
                model_used="none",
            )

        try:
            df[request.date_column] = pd.to_datetime(df[request.date_column], errors="coerce")
            df = df.dropna(subset=[request.date_column, request.target_column])
            df = df.sort_values(request.date_column)
        except Exception:
            pass

        if request.model == "auto" or request.model == "linear":
            predictions, metrics, model_name = self._linear_forecast(df, request)
        else:
            predictions, metrics, model_name = self._linear_forecast(df, request)

        pred_db = Prediction(
            dataset_id=dataset.id,
            target_column=request.target_column,
            model_type=model_name,
            forecast_horizon=request.horizon,
            forecast_data={"predictions": predictions},
            model_metrics=metrics,
        )
        self.db.add(pred_db)
        self.db.commit()

        return ForecastResult(
            dataset_id=dataset.id,
            target_column=request.target_column,
            horizon=request.horizon,
            predictions=predictions,
            model_used=model_name,
            metrics=metrics,
        )

    def _linear_forecast(self, df: pd.DataFrame, request: ForecastRequest):
        target = df[request.target_column].values.astype(float)
        n = len(target)
        X = np.arange(n).reshape(-1, 1)

        split = max(int(n * 0.8), 1)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = target[:split], target[split:]

        model = LinearRegression()
        model.fit(X_train, y_train)

        metrics: Dict[str, float] = {}
        if len(X_test) > 0:
            y_pred_test = model.predict(X_test)
            metrics["mae"] = round(float(mean_absolute_error(y_test, y_pred_test)), 4)
            metrics["rmse"] = round(float(np.sqrt(mean_squared_error(y_test, y_pred_test))), 4)

        future_X = np.arange(n, n + request.horizon).reshape(-1, 1)
        future_preds = model.predict(future_X)

        std = float(np.std(target))
        predictions = []
        for i, pred in enumerate(future_preds):
            predictions.append({
                "step": i + 1,
                "value": round(float(pred), 4),
                "lower": round(float(pred - 1.96 * std), 4),
                "upper": round(float(pred + 1.96 * std), 4),
            })

        return predictions, metrics, "linear_regression"
