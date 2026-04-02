from app.core.event_bus import EventBus
from app.core.service_registry import ServiceRegistry
from app.integrations.langchain_integration import get_langchain_tools
from app.integrations.langgraph_integration import build_quality_recommendation_graph


class DummyService:
    def __init__(self, response):
        self.response = response

    def execute(self, payload):
        return {"payload_keys": sorted(payload.keys()), **self.response}


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
    quality_result = tools[0]["callable"]("dataset-object")
    assert quality_result["type"] == "quality"


def test_langgraph_fallback_graph_without_langgraph():
    registry = ServiceRegistry()
    registry.register("quality", DummyService({"score": 88}))
    registry.register("recommendation", DummyService({"count": 3}))

    graph = build_quality_recommendation_graph(registry)
    result = graph({"dataset": object()})

    assert result["quality"]["score"] == 88
    assert result["recommendations"]["count"] == 3
