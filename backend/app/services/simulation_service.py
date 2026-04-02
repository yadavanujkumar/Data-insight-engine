from typing import Any, Dict

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import Dataset
from app.schemas.schemas import SimulationRequest, SimulationResult
from app.services.ingestion_service import IngestionService


class SimulationService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)

    def run(self, dataset: Dataset, request: SimulationRequest) -> SimulationResult:
        df = self.ingestion.load_dataframe(dataset)

        if request.simulation_type == "monte_carlo":
            return self._monte_carlo(df, request)
        return self._monte_carlo(df, request)

    def _monte_carlo(self, df: pd.DataFrame, request: SimulationRequest) -> SimulationResult:
        target = request.target_column
        n = request.n_simulations
        params = request.parameters

        if target in df.columns and df[target].dtype in [np.float64, np.int64]:
            series = df[target].dropna()
            mean = float(series.mean())
            std = float(series.std())
        else:
            mean = float(params.get("mean", 100.0))
            std = float(params.get("std", 10.0))

        growth_rate = float(params.get("growth_rate", 0.05))
        volatility = float(params.get("volatility", std / max(mean, 1)))
        horizon = int(params.get("horizon", 12))

        simulations = []
        for _ in range(n):
            path = [mean]
            for _ in range(horizon):
                shock = np.random.normal(growth_rate, volatility)
                path.append(path[-1] * (1 + shock))
            simulations.append(path[-1])

        simulations_arr = np.array(simulations)
        results_data = {
            "final_values": simulations[:100],
            "percentiles": {
                "p5": round(float(np.percentile(simulations_arr, 5)), 4),
                "p25": round(float(np.percentile(simulations_arr, 25)), 4),
                "p50": round(float(np.percentile(simulations_arr, 50)), 4),
                "p75": round(float(np.percentile(simulations_arr, 75)), 4),
                "p95": round(float(np.percentile(simulations_arr, 95)), 4),
            },
        }
        statistics = {
            "mean": round(float(simulations_arr.mean()), 4),
            "std": round(float(simulations_arr.std()), 4),
            "min": round(float(simulations_arr.min()), 4),
            "max": round(float(simulations_arr.max()), 4),
            "prob_positive_return": round(float((simulations_arr > mean).mean()), 4),
        }
        return SimulationResult(
            simulation_type="monte_carlo",
            n_simulations=n,
            results=results_data,
            statistics=statistics,
        )

    def what_if(self, dataset: Dataset, request: SimulationRequest) -> Dict[str, Any]:
        df = self.ingestion.load_dataframe(dataset)
        target = request.target_column
        params = request.parameters

        if target not in df.columns:
            return {"error": f"Column '{target}' not found"}

        base_value = float(df[target].mean()) if df[target].dtype in [np.float64, np.int64] else 0

        scenarios = {}
        for param_name, delta in params.items():
            try:
                delta_val = float(delta)
            except (TypeError, ValueError):
                continue
            scenarios[param_name] = {
                "base": round(base_value, 4),
                "adjusted": round(base_value * (1 + delta_val), 4),
                "change_pct": round(delta_val * 100, 2),
            }

        return {
            "target_column": target,
            "base_value": round(base_value, 4),
            "scenarios": scenarios,
        }
