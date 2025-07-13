from abc import ABC, abstractmethod

from schemas.safety_guards import SafetyGuardResult


class SafetyGuard(ABC):
    @abstractmethod
    def check_safety(self, text: str) -> SafetyGuardResult:
        pass
