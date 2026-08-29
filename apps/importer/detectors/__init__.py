from ..formats import SUPPORTED_FORMATS

from .file_detector import (
    DetectedFile,
    detect_file,
)

__all__ = [
    "SUPPORTED_FORMATS",
    "DetectedFile",
    "detect_file",
]
