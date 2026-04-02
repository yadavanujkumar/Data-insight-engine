from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.models.db_models import Alert, MetricSnapshot
from app.schemas.schemas import AlertCreate


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, alert_data: AlertCreate) -> Alert:
        alert = Alert(
            name=alert_data.name,
            description=alert_data.description,
            severity=alert_data.severity,
            metric_name=alert_data.metric_name,
            threshold_value=alert_data.threshold_value,
            rule_config=alert_data.rule_config or {},
            status="active",
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def resolve_alert(self, alert_id: int) -> Alert:
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def check_all_alerts(self) -> Dict[str, Any]:
        active_alerts = self.db.query(Alert).filter(Alert.status == "active").all()
        triggered = []

        for alert in active_alerts:
            latest = (
                self.db.query(MetricSnapshot)
                .filter(MetricSnapshot.metric_name == alert.metric_name)
                .order_by(MetricSnapshot.recorded_at.desc())
                .first()
            )
            if not latest:
                continue

            rule = alert.rule_config or {}
            operator = rule.get("operator", "gt")
            threshold = alert.threshold_value
            current = latest.metric_value

            triggered_now = False
            if operator == "gt" and current > threshold:
                triggered_now = True
            elif operator == "lt" and current < threshold:
                triggered_now = True
            elif operator == "gte" and current >= threshold:
                triggered_now = True
            elif operator == "lte" and current <= threshold:
                triggered_now = True

            if triggered_now:
                alert.current_value = current
                alert.triggered_at = datetime.utcnow()
                alert.status = "active"
                self.db.commit()
                triggered.append({"alert_id": alert.id, "name": alert.name, "current_value": current})

        return {"checked": len(active_alerts), "triggered": triggered}
