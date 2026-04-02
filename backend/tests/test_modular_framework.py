import pandas as pd

from app.core.event_bus import EventBus
from app.core.event_bus import event_bus as global_event_bus
from app.core.service_registry import ServiceRegistry
from app.integrations.langchain_integration import get_langchain_tools
from app.integrations.langgraph_integration import build_quality_recommendation_graph
from app.services.analytics_service import AnalyticsService
from app.services.ingestion_service import IngestionService
from app.services.quality_service import QualityService
from app.services.recommendation_service import RecommendationService


class DummyDataset:
    def __init__(self, dataset_id=1):
        self.id = dataset_id


class DummyService:
    def __init__(self, response):
        self.response = response

    def execute(self, payload):
        return {"payload_keys": sorted(payload.keys()), **self.response}


class DummyModelDump:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self):
        return self.payload


class DummyDB:
    def __init__(self):
        self._refresh_id = 1

    def add(self, _obj):
        pass

    def commit(self):
        pass

    def refresh(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = self._refresh_id
            self._refresh_id += 1


def test_event_bus_publish_to_multiple_subscribers():
    bus = EventBus()
    calls = []

    def handler_one(payload):
        calls.append(("one", payload["dataset_id"]))

    def handler_two(payload):
        calls.append(("two", payload["dataset_id"]))

    bus.subscribe("dataset.ingested", handler_one)
    bus.subscribe("dataset.ingested", handler_two)
    bus.publish("dataset.ingested", {"dataset_id": 7})

    assert calls == [("one", 7), ("two", 7)]


def test_service_registry_register_and_get():
    registry = ServiceRegistry()
    service = DummyService({"ok": True})
    registry.register("quality", service)

    assert registry.get("quality") is service
    assert "quality" in registry.all()


def test_langchain_tools_fallback_without_langchain():
    registry = ServiceRegistry()
    registry.register("quality", DummyService({"type": "quality"}))
    registry.register("recommendation", DummyService({"type": "recommendation"}))

    tools = get_langchain_tools(registry)

    assert len(tools) == 2
    assert all(tool["provider"] == "fallback" for tool in tools)
    quality_result = tools[0]["callable"](DummyDataset())
    assert quality_result["type"] == "quality"


def test_langgraph_fallback_graph_without_langgraph():
    registry = ServiceRegistry()
    registry.register("quality", DummyService({"score": 88}))
    registry.register("recommendation", DummyService({"count": 3}))

    graph = build_quality_recommendation_graph(registry)
    result = graph({"dataset": DummyDataset()})

    assert result["quality"]["score"] == 88
    assert result["recommendations"]["count"] == 3


def test_quality_service_execute_missing_dataset():
    service = QualityService(db=DummyDB())
    assert service.execute({}) == {"error": "dataset is required"}


def test_quality_service_execute_valid_dataset(monkeypatch):
    service = QualityService(db=DummyDB())
    monkeypatch.setattr(
        service, "compute_quality", lambda dataset: DummyModelDump({"overall_score": 90.0, "dataset_id": dataset.id})
    )
    result = service.execute({"dataset": DummyDataset(3)})
    assert result["overall_score"] == 90.0
    assert result["dataset_id"] == 3


def test_analytics_service_execute_missing_fields():
    service = AnalyticsService(db=DummyDB())
    assert service.execute({}) == {"error": "dataset and request are required"}


def test_analytics_service_execute_valid(monkeypatch):
    service = AnalyticsService(db=DummyDB())
    monkeypatch.setattr(
        service,
        "run_analytics",
        lambda dataset, request: DummyModelDump({"dataset_id": dataset.id, "target_column": request["target"]}),
    )
    result = service.execute({"dataset": DummyDataset(5), "request": {"target": "revenue"}})
    assert result == {"dataset_id": 5, "target_column": "revenue"}


def test_ingestion_service_execute_missing_fields():
    service = IngestionService(db=DummyDB())
    assert service.execute({}) == {"error": "content, filename, and name are required"}


def test_ingestion_service_execute_valid(monkeypatch):
    service = IngestionService(db=DummyDB())
    monkeypatch.setattr(
        service,
        "ingest_file",
        lambda content, filename, name, description=None: type("D", (), {"id": 11, "status": "ready"})(),
    )
    result = service.execute({"content": b"a,b\n1,2\n", "filename": "a.csv", "name": "sample"})
    assert result == {"dataset_id": 11, "status": "ready"}


def test_ingestion_service_ingest_file_publishes_event(tmp_path, monkeypatch):
    service = IngestionService(db=DummyDB())
    monkeypatch.setattr("app.services.ingestion_service.settings.UPLOAD_DIR", str(tmp_path))
    events = []
    monkeypatch.setattr(global_event_bus, "publish", lambda event_name, payload: events.append((event_name, payload)))

    dataset = service.ingest_file(
        content=b"col1,col2\n1,2\n",
        filename="test.csv",
        name="demo",
        description="demo",
    )

    assert dataset.id == 1
    assert events == [("dataset.ingested", {"dataset_id": 1, "name": "demo"})]


def test_recommendation_service_execute_missing_dataset():
    service = RecommendationService(db=DummyDB())
    assert service.execute({}) == {"error": "dataset is required"}


def test_recommendation_service_generate_publishes_event(monkeypatch):
    service = RecommendationService(db=DummyDB())
    monkeypatch.setattr(
        service.ingestion,
        "load_dataframe",
        lambda dataset: pd.DataFrame({"v": [1, 2, 2, 100, None]}),
    )
    monkeypatch.setattr(
        service.quality_svc,
        "compute_quality",
        lambda dataset: type("Q", (), {"column_profiles": {"v": {"null_pct": 40.0}}, "overall_score": 60.0})(),
    )
    events = []
    monkeypatch.setattr(global_event_bus, "publish", lambda event_name, payload: events.append((event_name, payload)))

    dataset = DummyDataset(22)
    recs = service.generate(dataset)

    assert len(recs) > 0
    assert events == [
        ("recommendations.generated", {"dataset_id": 22, "recommendation_count": len(recs)})
    ]
