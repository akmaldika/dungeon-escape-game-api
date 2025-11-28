"""
Port configuration for FastAPI server.
Supports custom port selection via command-line or environment variables.
"""

from __future__ import annotations

import os
import socket
from typing import Optional


# Default port
DEFAULT_PORT = 8000

# Port range for non-privileged applications
MIN_PORT = 1024
MAX_PORT = 65535

# Reserved/commonly used ports to warn about
RESERVED_PORTS = {
    80: "HTTP",
    443: "HTTPS",
    3000: "Common dev server",
    5000: "Flask default",
    8080: "Common HTTP alt",
    9000: "Common service",
}


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is available on the given host.
    
    Args:
        port: Port number to check
        host: Host address (default: 0.0.0.0)
    
    Returns:
        True if port is available, False if in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.connect_ex((host, port))
            return result != 0  # 0 means connected (port in use)
    except Exception:
        return False


def validate_port(port: int) -> tuple[bool, Optional[str]]:
    """Validate a port number.
    
    Args:
        port: Port number to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False if invalid
        - error_message: Error description if invalid, None if valid
    """
    if not isinstance(port, int):
        return False, f"Port must be integer, got {type(port).__name__}"
    
    if port < MIN_PORT or port > MAX_PORT:
        return False, f"Port must be in range {MIN_PORT}-{MAX_PORT}, got {port}"
    
    if port in RESERVED_PORTS:
        return True, f"⚠ Warning: Port {port} ({RESERVED_PORTS[port]}) is commonly used"
    
    return True, None


def get_port_from_env() -> int:
    """Get port from environment variable.
    
    Checks API_PORT environment variable.
    
    Returns:
        Port number from env, or DEFAULT_PORT if not set or invalid
    """
    port_str = os.getenv("API_PORT", str(DEFAULT_PORT))
    try:
        port = int(port_str)
        is_valid, msg = validate_port(port)
        if is_valid:
            return port
    except ValueError:
        pass
    
    return DEFAULT_PORT


def find_available_port(start_port: int = DEFAULT_PORT, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port.
    
    Increments port number until an available one is found.
    
    Args:
        start_port: Port to start searching from (default: 8000)
        max_attempts: Maximum ports to try (default: 10)
    
    Returns:
        First available port found
        
    Raises:
        RuntimeError: If no available port found within max_attempts
    """
    for offset in range(max_attempts):
        port = start_port + offset
        if is_port_available(port):
            return port
    
    raise RuntimeError(
        f"Could not find available port in range {start_port}-{start_port + max_attempts - 1}"
    )


__all__ = [
    "DEFAULT_PORT",
    "MIN_PORT",
    "MAX_PORT",
    "RESERVED_PORTS",
    "is_port_available",
    "validate_port",
    "get_port_from_env",
    "find_available_port",
]
