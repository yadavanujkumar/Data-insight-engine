from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, EmailStr


# ── User ──────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dataset ───────────────────────────────────────────────────────────────────

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetRead(DatasetBase):
    id: int
    file_type: Optional[str]
    row_count: Optional[int]
    column_count: Optional[int]
    column_info: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Cleaning ──────────────────────────────────────────────────────────────────

class CleaningRequest(BaseModel):
    dataset_id: int
    operations: List[str] = ["missing_values", "duplicates", "outliers"]
    strategy: str = "auto"


class CleaningResult(BaseModel):
    dataset_id: int
    operations_performed: List[str]
    rows_before: int
    rows_after: int
    columns_modified: List[str]
    report: Dict[str, Any]


class CleaningLogRead(BaseModel):
    id: int
    dataset_id: int
    operation: str
    details: Optional[Dict[str, Any]]
    rows_affected: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Quality ───────────────────────────────────────────────────────────────────

class QualityScore(BaseModel):
    overall_score: float
    completeness: float
    consistency: float
    validity: float
    uniqueness: float
    column_profiles: Dict[str, Any]
    issues: List[Dict[str, Any]]


# ── Graph ─────────────────────────────────────────────────────────────────────

class EntityCreate(BaseModel):
    name: str
    entity_type: str
    properties: Optional[Dict[str, Any]] = None
    dataset_id: Optional[int] = None


class EntityRead(EntityCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class RelationshipCreate(BaseModel):
    source_id: int
    target_id: int
    relationship_type: str
    weight: float = 1.0
    properties: Optional[Dict[str, Any]] = None


class RelationshipRead(RelationshipCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsRequest(BaseModel):
    dataset_id: int
    target_column: str
    group_by: Optional[List[str]] = None
    date_column: Optional[str] = None
    operations: List[str] = ["summary", "trend", "anomalies"]


class AnalyticsResult(BaseModel):
    dataset_id: int
    target_column: str
    summary: Dict[str, Any]
    trends: Optional[Dict[str, Any]] = None
    anomalies: Optional[List[Dict[str, Any]]] = None
    kpis: Optional[Dict[str, Any]] = None


# ── Forecasting ───────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    dataset_id: int
    target_column: str
    date_column: str
    horizon: int = 30
    frequency: str = "D"
    model: str = "auto"


class ForecastResult(BaseModel):
    dataset_id: int
    target_column: str
    horizon: int
    predictions: List[Dict[str, Any]]
    confidence_intervals: Optional[List[Dict[str, Any]]] = None
    model_used: str
    metrics: Optional[Dict[str, float]] = None


# ── Simulation ────────────────────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    dataset_id: int
    target_column: str
    parameters: Dict[str, Any]
    n_simulations: int = 1000
    simulation_type: str = "monte_carlo"


class SimulationResult(BaseModel):
    simulation_type: str
    n_simulations: int
    results: Dict[str, Any]
    statistics: Dict[str, float]


# ── Recommendations ───────────────────────────────────────────────────────────

class RecommendationRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    priority: str
    expected_impact: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None


# ── NLQ ───────────────────────────────────────────────────────────────────────

class NLQRequest(BaseModel):
    query: str
    dataset_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class NLQResponse(BaseModel):
    query: str
    interpretation: str
    result: Optional[Any] = None
    sql_query: Optional[str] = None
    explanation: str


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertCreate(BaseModel):
    name: str
    description: Optional[str] = None
    severity: str = "warning"
    metric_name: str
    threshold_value: float
    rule_config: Optional[Dict[str, Any]] = None


class AlertRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    severity: str
    status: str
    metric_name: str
    threshold_value: float
    current_value: Optional[float]
    triggered_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    title: str
    description: Optional[str] = None
    report_type: str
    dataset_id: Optional[int] = None


class ReportRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    report_type: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Metrics ───────────────────────────────────────────────────────────────────

class MetricSnapshotCreate(BaseModel):
    metric_name: str
    metric_value: float
    labels: Optional[Dict[str, str]] = None


class MetricSnapshotRead(MetricSnapshotCreate):
    id: int
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ── Generic ───────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]
