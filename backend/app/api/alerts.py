from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Alert
from app.schemas.schemas import AlertCreate, AlertRead
from app.services.alert_service import AlertService

router = APIRouter()


@router.post("/alerts", response_model=AlertRead)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    service = AlertService(db)
    return service.create_alert(alert)


@router.get("/alerts", response_model=List[AlertRead])
def list_alerts(status: str = None, severity: str = None, db: Session = Depends(get_db)):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.created_at.desc()).limit(100).all()


@router.get("/alerts/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/alerts/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    service = AlertService(db)
    return service.resolve_alert(alert_id)


@router.post("/alerts/check")
def check_alerts(db: Session = Depends(get_db)):
    service = AlertService(db)
    return service.check_all_alerts()
