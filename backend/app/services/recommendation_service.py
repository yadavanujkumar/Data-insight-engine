from typing import Any, Dict, List

import numpy as np
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, Recommendation
from app.services.ingestion_service import IngestionService
from app.services.quality_service import QualityService


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionService(db)
        self.quality_svc = QualityService(db)

    def generate(self, dataset: Dataset) -> List[Recommendation]:
        df = self.ingestion.load_dataframe(dataset)
        recs: List[Dict[str, Any]] = []

        if df.empty:
            return []

        quality = self.quality_svc.compute_quality(dataset)

        # Missing data recommendations
        for col, profile in quality.column_profiles.items():
            null_pct = profile.get("null_pct", 0)
            if null_pct > 30:
                recs.append({
                    "title": f"High missing data in '{col}'",
                    "description": f"Column '{col}' has {null_pct:.1f}% missing values. Consider imputation or removal.",
                    "category": "data_quality",
                    "priority": "high" if null_pct > 50 else "medium",
                    "expected_impact": min(null_pct / 100, 1.0),
                })

        # Quality score recommendation
        if quality.overall_score < 70:
            recs.append({
                "title": "Overall data quality is low",
                "description": f"Data quality score is {quality.overall_score:.1f}/100. Run data cleaning to improve.",
                "category": "data_quality",
                "priority": "high",
                "expected_impact": 0.8,
            })

        # Outlier recommendations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
            if outliers / max(len(df), 1) > 0.05:
                recs.append({
                    "title": f"Outliers detected in '{col}'",
                    "description": f"{outliers} outliers detected ({outliers / len(df) * 100:.1f}%). Review or clip these values.",
                    "category": "analytics",
                    "priority": "medium",
                    "expected_impact": 0.5,
                })

        # Duplicate recommendation
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            recs.append({
                "title": "Duplicate rows detected",
                "description": f"{dup_count} duplicate rows found. Remove duplicates for accurate analysis.",
                "category": "data_quality",
                "priority": "medium",
                "expected_impact": 0.4,
            })

        # Sort by impact
        recs.sort(key=lambda r: r["expected_impact"], reverse=True)

        db_recs = []
        for r in recs[:10]:
            rec = Recommendation(
                title=r["title"],
                description=r["description"],
                category=r["category"],
                priority=r["priority"],
                expected_impact=r["expected_impact"],
                dataset_id=dataset.id,
                status="pending",
            )
            self.db.add(rec)
            db_recs.append(rec)

        self.db.commit()
        for rec in db_recs:
            self.db.refresh(rec)
        return db_recs
