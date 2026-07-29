"""Azure DevOps HTTP client package."""

from __future__ import annotations

from qa_intelligence.infrastructure.ado.auth import AuthProvider, PatAuthProvider
from qa_intelligence.infrastructure.ado.client import AzureDevOpsClient

__all__ = [
    "AuthProvider",
    "AzureDevOpsClient",
    "PatAuthProvider",
]
