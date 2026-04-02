from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset, Recommendation
from app.schemas.schemas import RecommendationRead, RecommendationUpdate
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("/recommendations/generate/{dataset_id}", response_model=List[RecommendationRead])
def generate_recommendations(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = RecommendationService(db)
    return service.generate(dataset)


@router.get("/recommendations", response_model=List[RecommendationRead])
def list_recommendations(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Recommendation).offset(skip).limit(limit).all()


@router.patch("/recommendations/{rec_id}", response_model=RecommendationRead)
def update_recommendation(rec_id: int, update: RecommendationUpdate, db: Session = Depends(get_db)):
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if update.status:
        rec.status = update.status
    if update.priority:
        rec.priority = update.priority
    db.commit()
    db.refresh(rec)
    return rec
