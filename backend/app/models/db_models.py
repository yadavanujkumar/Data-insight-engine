from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="owner")
    reports = relationship("Report", back_populates="owner")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    file_path = Column(String)
    file_type = Column(String)
    row_count = Column(Integer)
    column_count = Column(Integer)
    column_info = Column(JSON)
    quality_score = Column(Float)
    status = Column(String, default="pending")  # pending, processing, ready, error
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="datasets")
    cleaning_logs = relationship("CleaningLog", back_populates="dataset")
    predictions = relationship("Prediction", back_populates="dataset")


class CleaningLog(Base):
    __tablename__ = "cleaning_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    operation = Column(String, nullable=False)
    details = Column(JSON)
    rows_affected = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="cleaning_logs")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    properties = Column(JSON)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_relationships = relationship(
        "Relationship", foreign_keys="Relationship.source_id", back_populates="source"
    )
    target_relationships = relationship(
        "Relationship", foreign_keys="Relationship.target_id", back_populates="target"
    )


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    relationship_type = Column(String, nullable=False)
    weight = Column(Float, default=1.0)
    properties = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship(
        "Entity", foreign_keys=[source_id], back_populates="source_relationships"
    )
    target = relationship(
        "Entity", foreign_keys=[target_id], back_populates="target_relationships"
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    target_column = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    forecast_horizon = Column(Integer)
    forecast_data = Column(JSON)
    model_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="predictions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    priority = Column(String, default="medium")  # low, medium, high, critical
    expected_impact = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending, in_progress, completed, dismissed
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, default="info")  # info, warning, critical
    status = Column(String, default="active")  # active, resolved, acknowledged
    metric_name = Column(String)
    threshold_value = Column(Float)
    current_value = Column(Float)
    rule_config = Column(JSON)
    triggered_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    labels = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    report_type = Column(String, nullable=False)
    content = Column(JSON)
    status = Column(String, default="draft")  # draft, published, archived
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="reports")
