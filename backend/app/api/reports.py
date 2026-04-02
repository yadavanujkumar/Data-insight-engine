from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Report
from app.schemas.schemas import ReportCreate, ReportRead
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.post("/reports", response_model=ReportRead)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    db_report = Report(
        title=report.title,
        description=report.description,
        report_type=report.report_type,
        dataset_id=report.dataset_id,
        content={},
        status="draft",
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report


@router.get("/reports", response_model=List[ReportRead])
def list_reports(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(Report).offset(skip).limit(limit).all()


@router.get("/reports/{report_id}", response_model=ReportRead)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}
