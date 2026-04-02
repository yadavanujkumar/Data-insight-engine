from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import DatasetRead, MessageResponse
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/datasets/upload", response_model=DatasetRead)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db),
):
    if file.content_type not in [
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/plain",
    ]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or Excel.")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    service = IngestionService(db)
    dataset = service.ingest_file(
        content=content,
        filename=file.filename,
        name=name or file.filename,
        description=description,
    )
    return dataset


@router.get("/datasets", response_model=List[DatasetRead])
def list_datasets(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Dataset).offset(skip).limit(limit).all()


@router.get("/datasets/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.delete("/datasets/{dataset_id}", response_model=MessageResponse)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    db.delete(dataset)
    db.commit()
    return {"message": f"Dataset {dataset_id} deleted successfully"}


@router.get("/datasets/{dataset_id}/preview")
def preview_dataset(dataset_id: int, rows: int = 10, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    service = IngestionService(db)
    return service.get_preview(dataset, rows)
