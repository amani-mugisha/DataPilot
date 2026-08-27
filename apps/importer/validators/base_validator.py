from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class BaseValidator(ABC):
    """Abstract interface for all DataPilot file validators."""

    @abstractmethod
    def validate(
        self,
        file_path: str | Path | BinaryIO,
        filename: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """Validate a supported file before it is read."""
        raise NotImplementedError
