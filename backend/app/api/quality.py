from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import QualityScore
from app.services.quality_service import QualityService

router = APIRouter()


@router.get("/quality/{dataset_id}", response_model=QualityScore)
def get_quality_score(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = QualityService(db)
    return service.compute_quality(dataset)


@router.get("/quality/{dataset_id}/profile")
def get_column_profile(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = QualityService(db)
    return service.column_profile(dataset)


@router.get("/quality/{dataset_id}/drift")
def detect_drift(dataset_id: int, reference_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    reference = db.query(Dataset).filter(Dataset.id == reference_id).first()
    if not dataset or not reference:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = QualityService(db)
    return service.detect_drift(dataset, reference)
