"""MCP runtime — lazy DI container for tool handlers."""

from __future__ import annotations

from qa_intelligence.infrastructure.config import clear_settings_cache, get_settings
from qa_intelligence.infrastructure.di import Container, build_container
from qa_intelligence.infrastructure.errors import ConfigurationError

_container: Container | None = None


def get_container() -> Container:
    """Return the process-wide container, building it on first use.

    Requires ``ADO_ORGANIZATION``, ``ADO_PROJECT``, and ``ADO_PAT`` in the
    environment or ``.env`` file. Missing credentials raise ``ConfigurationError``.
    """
    global _container
    if _container is None:
        try:
            settings = get_settings()
        except Exception as exc:  # noqa: BLE001
            raise ConfigurationError(
                "Azure DevOps settings could not be loaded. "
                "Set ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT in .env "
                "(see .env.example).",
                details={"cause": type(exc).__name__},
            ) from exc

        if (
            not settings.ado_organization.strip()
            or not settings.ado_project.strip()
            or not settings.ado_pat.strip()
        ):
            raise ConfigurationError(
                "Azure DevOps credentials are missing. "
                "Set ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT in .env "
                "(see .env.example).",
            )

        try:
            _container = build_container(settings)
        except Exception as exc:  # noqa: BLE001
            raise ConfigurationError(
                "Failed to initialize Azure DevOps client. "
                "Check ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT.",
                details={"cause": type(exc).__name__, "message": str(exc)},
            ) from exc
    return _container


def reset_container() -> None:
    """Drop the cached container (tests / credential reload)."""
    global _container
    _container = None
    clear_settings_cache()
