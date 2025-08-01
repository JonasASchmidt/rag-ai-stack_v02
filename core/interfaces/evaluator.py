"""Interfaces for evaluating generated responses."""

from abc import ABC, abstractmethod
from typing import Sequence


class Evaluator(ABC):
    """Abstract base class for evaluating responses."""

    @abstractmethod
    def evaluate(self, query: str, response: str, references: Sequence[str]) -> float:
        """Return a score for ``response`` given ``query`` and reference documents."""
