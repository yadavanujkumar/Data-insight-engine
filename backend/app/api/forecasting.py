from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import ForecastRequest, ForecastResult
from app.services.forecasting_service import ForecastingService

router = APIRouter()


@router.post("/forecasting/run", response_model=ForecastResult)
def run_forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = ForecastingService(db)
    return service.forecast(dataset, request)


@router.get("/forecasting/history/{dataset_id}")
def get_forecast_history(dataset_id: int, db: Session = Depends(get_db)):
    from app.models.db_models import Prediction
    preds = (
        db.query(Prediction)
        .filter(Prediction.dataset_id == dataset_id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    return [
        {
            "id": p.id,
            "target_column": p.target_column,
            "model_type": p.model_type,
            "horizon": p.forecast_horizon,
            "created_at": p.created_at,
        }
        for p in preds
    ]
