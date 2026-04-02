from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import AnalyticsRequest, AnalyticsResult
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.post("/analytics/run", response_model=AnalyticsResult)
def run_analytics(request: AnalyticsRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = AnalyticsService(db)
    return service.run_analytics(dataset, request)


@router.get("/analytics/{dataset_id}/kpis")
def get_kpis(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = AnalyticsService(db)
    return service.compute_kpis(dataset)


@router.get("/analytics/{dataset_id}/anomalies")
def detect_anomalies(dataset_id: int, column: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = AnalyticsService(db)
    return service.detect_anomalies(dataset, column)
