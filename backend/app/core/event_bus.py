from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


class EventBus:
    def __init__(self):
        self._subscribers: DefaultDict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Any], None]) -> None:
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, payload: Any) -> None:
        for handler in self._subscribers.get(event_name, []):
            handler(payload)

    def reset(self) -> None:
        self._subscribers.clear()


event_bus = EventBus()
