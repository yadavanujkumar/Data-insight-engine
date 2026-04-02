from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import CleaningLogRead, CleaningRequest, CleaningResult
from app.services.cleaning_service import CleaningService

router = APIRouter()


@router.post("/cleaning/run", response_model=CleaningResult)
def run_cleaning(request: CleaningRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = CleaningService(db)
    return service.run_cleaning(dataset, request)


@router.get("/cleaning/logs/{dataset_id}", response_model=List[CleaningLogRead])
def get_cleaning_logs(dataset_id: int, db: Session = Depends(get_db)):
    from app.models.db_models import CleaningLog
    logs = db.query(CleaningLog).filter(CleaningLog.dataset_id == dataset_id).all()
    return logs
