"""Interface for scoring the quality of generated answers."""

from abc import ABC, abstractmethod


class Evaluator(ABC):
    """Abstract base class for evaluating question/answer pairs."""

    @abstractmethod
    def evaluate(self, answer: str, expected: str) -> float:
        """Return a similarity score between ``answer`` and ``expected``."""
