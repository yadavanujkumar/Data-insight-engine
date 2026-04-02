from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

from app.core.service_registry import service_registry
from app.api import (
    alerts,
    analytics,
    cleaning,
    forecasting,
    graph,
    ingestion,
    metrics,
    nlq,
    quality,
    recommendations,
    reports,
    simulation,
)
from app.config import settings
from app.services.analytics_service import AnalyticsService
from app.services.ingestion_service import IngestionService
from app.services.quality_service import QualityService
from app.services.recommendation_service import RecommendationService


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # Register service classes for modular orchestration/integrations
    service_registry.register("ingestion", IngestionService)
    service_registry.register("quality", QualityService)
    service_registry.register("analytics", AnalyticsService)
    service_registry.register("recommendation", RecommendationService)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready Decision Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Register routers
prefix = settings.API_V1_STR
app.include_router(ingestion.router, prefix=prefix, tags=["ingestion"])
app.include_router(cleaning.router, prefix=prefix, tags=["cleaning"])
app.include_router(quality.router, prefix=prefix, tags=["quality"])
app.include_router(graph.router, prefix=prefix, tags=["graph"])
app.include_router(analytics.router, prefix=prefix, tags=["analytics"])
app.include_router(forecasting.router, prefix=prefix, tags=["forecasting"])
app.include_router(simulation.router, prefix=prefix, tags=["simulation"])
app.include_router(recommendations.router, prefix=prefix, tags=["recommendations"])
app.include_router(nlq.router, prefix=prefix, tags=["nlq"])
app.include_router(alerts.router, prefix=prefix, tags=["alerts"])
app.include_router(reports.router, prefix=prefix, tags=["reports"])
app.include_router(metrics.router, prefix=prefix, tags=["metrics"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "platform": settings.APP_NAME, "version": "1.0.0"}
