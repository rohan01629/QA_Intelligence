"""CoverageService module — delegates to CoverageAnalysisService."""

from __future__ import annotations

from qa_intelligence.services.coverage_analysis_service import CoverageAnalysisService

CoverageService = CoverageAnalysisService

__all__ = ["CoverageAnalysisService", "CoverageService"]
