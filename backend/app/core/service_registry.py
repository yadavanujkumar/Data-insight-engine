from typing import Any, Dict


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        return self._services.get(name)

    def resolve(self, name: str, **kwargs: Any) -> Any:
        service = self.get(name)
        if service is None:
            return None
        if hasattr(service, "execute"):
            return service
        if isinstance(service, type):
            db = kwargs.get("db")
            if db is None:
                raise ValueError(f"db is required to instantiate service '{name}'")
            return service(db)
        if callable(service):
            return service(**kwargs)
        return service

    def all(self) -> Dict[str, Any]:
        return dict(self._services)

    def clear(self) -> None:
        self._services.clear()


service_registry = ServiceRegistry()
