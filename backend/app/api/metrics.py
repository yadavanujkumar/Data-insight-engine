from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import MetricSnapshot
from app.schemas.schemas import MetricSnapshotCreate, MetricSnapshotRead

router = APIRouter()


@router.post("/metrics/record", response_model=MetricSnapshotRead)
def record_metric(metric: MetricSnapshotCreate, db: Session = Depends(get_db)):
    snapshot = MetricSnapshot(
        metric_name=metric.metric_name,
        metric_value=metric.metric_value,
        labels=metric.labels,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/metrics/{metric_name}", response_model=List[MetricSnapshotRead])
def get_metric_history(
    metric_name: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return (
        db.query(MetricSnapshot)
        .filter(MetricSnapshot.metric_name == metric_name)
        .order_by(MetricSnapshot.recorded_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/metrics")
def list_metrics(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(
        MetricSnapshot.metric_name,
        func.count(MetricSnapshot.id).label("count"),
        func.avg(MetricSnapshot.metric_value).label("avg"),
        func.max(MetricSnapshot.metric_value).label("max"),
        func.min(MetricSnapshot.metric_value).label("min"),
    ).group_by(MetricSnapshot.metric_name).all()

    return [
        {
            "metric_name": r.metric_name,
            "count": r.count,
            "avg": round(r.avg, 4) if r.avg else None,
            "max": r.max,
            "min": r.min,
        }
        for r in results
    ]
