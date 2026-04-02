from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseService(ABC):
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
