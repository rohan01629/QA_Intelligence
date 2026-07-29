"""DuplicateService module — delegates to DuplicateDetectionService."""

from __future__ import annotations

from qa_intelligence.services.duplicate_detection_service import DuplicateDetectionService

DuplicateService = DuplicateDetectionService

__all__ = ["DuplicateDetectionService", "DuplicateService"]
