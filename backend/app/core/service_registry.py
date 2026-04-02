from typing import Any, Dict


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        return self._services.get(name)

    def all(self) -> Dict[str, Any]:
        return dict(self._services)

    def clear(self) -> None:
        self._services.clear()


service_registry = ServiceRegistry()
