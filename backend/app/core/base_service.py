from abc import ABC
from typing import Any, Dict


class BaseService(ABC):
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
