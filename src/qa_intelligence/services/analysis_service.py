"""AnalysisService module — delegates to RequirementAnalysisService."""

from __future__ import annotations

from qa_intelligence.services.requirement_analysis_service import RequirementAnalysisService

AnalysisService = RequirementAnalysisService

__all__ = ["AnalysisService", "RequirementAnalysisService"]
