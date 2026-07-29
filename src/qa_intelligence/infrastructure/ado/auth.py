"""Azure DevOps authentication providers."""

from __future__ import annotations

import base64
from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthProvider(Protocol):
    """Port for supplying HTTP Authorization headers."""

    def get_authorization_header(self) -> dict[str, str]:
        """Return headers that authenticate requests to Azure DevOps."""
        ...


class PatAuthProvider:
    """Authenticate with an Azure DevOps Personal Access Token (Basic)."""

    def __init__(self, pat: str) -> None:
        if not pat or not pat.strip():
            raise ValueError("PAT must not be blank")
        self._pat = pat.strip()

    def get_authorization_header(self) -> dict[str, str]:
        # Azure DevOps expects Basic auth with empty username and PAT as password.
        token = base64.b64encode(f":{self._pat}".encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {token}"}
