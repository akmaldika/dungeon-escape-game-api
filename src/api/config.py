from __future__ import annotations

import os
from typing import List, Tuple


def _parse_origins(value: str | None) -> List[str]:
    if not value:
        return ["*"]
    parts = [p.strip() for p in value.split(",")]
    return [p for p in parts if p]


def get_server_settings() -> Tuple[str, int, List[str]]:
    """Return (host, port, cors_origins) from environment with safe defaults.

    API_HOST: default 0.0.0.0 (listen on all interfaces)
    API_PORT: default 8000
    CORS_ORIGINS: comma-separated list or '*' for all, default '*'
    """
    host = os.getenv("API_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("API_PORT", "8000"))
    except ValueError:
        port = 8000
    cors = _parse_origins(os.getenv("CORS_ORIGINS"))
    return host, port, cors


__all__ = ["get_server_settings"]
