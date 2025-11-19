"""
URL validation utilities for SSRF protection.

Prevents Server-Side Request Forgery attacks by blocking requests to:
- Private IP ranges (RFC 1918)
- Localhost and loopback addresses
- Link-local addresses
- AWS metadata endpoints
- Other sensitive internal resources
"""

import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse


class SSRFProtectionError(Exception):
    """Raised when URL fails SSRF protection checks."""

    pass


# Dangerous IP ranges that should be blocked
BLOCKED_IP_RANGES = [
    ipaddress.IPv4Network("0.0.0.0/8"),  # Current network
    ipaddress.IPv4Network("10.0.0.0/8"),  # Private network
    ipaddress.IPv4Network("127.0.0.0/8"),  # Loopback
    ipaddress.IPv4Network("169.254.0.0/16"),  # Link-local (AWS metadata)
    ipaddress.IPv4Network("172.16.0.0/12"),  # Private network
    ipaddress.IPv4Network("192.168.0.0/16"),  # Private network
    ipaddress.IPv4Network("224.0.0.0/4"),  # Multicast
    ipaddress.IPv4Network("240.0.0.0/4"),  # Reserved
    ipaddress.IPv6Network("::1/128"),  # IPv6 loopback
    ipaddress.IPv6Network("fc00::/7"),  # IPv6 private
    ipaddress.IPv6Network("fe80::/10"),  # IPv6 link-local
]

# Blocked hostnames
BLOCKED_HOSTNAMES = {
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
    "::1",
    "[::1]",
    "metadata.google.internal",  # GCP metadata
    "169.254.169.254",  # AWS metadata
}


def is_ip_blocked(ip_str: str) -> bool:
    """
    Check if an IP address is in a blocked range.

    Args:
        ip_str: IP address string

    Returns:
        True if IP is blocked, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                return True
        return False
    except ValueError:
        # Not a valid IP address
        return False


def validate_url_ssrf(url: str) -> Tuple[bool, str]:
    """
    Validate URL against SSRF attacks.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if URL is safe
        - (False, error_message) if URL is dangerous
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return False, f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed."

        # Get hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "URL must contain a valid hostname"

        # Check against blocked hostnames
        hostname_lower = hostname.lower()
        if hostname_lower in BLOCKED_HOSTNAMES:
            return False, f"Access to {hostname} is blocked for security reasons"

        # Resolve hostname to IP and check if it's blocked
        try:
            # Get all IP addresses for this hostname
            addr_info = socket.getaddrinfo(hostname, None)
            for addr in addr_info:
                ip_str = addr[4][0]
                if is_ip_blocked(ip_str):
                    return (
                        False,
                        f"Access to {hostname} ({ip_str}) is blocked - private/internal IP address",
                    )
        except socket.gaierror:
            # DNS resolution failed - allow it to fail naturally later
            pass

        return True, ""

    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def validate_url_ssrf_strict(url: str) -> None:
    """
    Strict URL validation that raises exception on failure.

    Args:
        url: URL to validate

    Raises:
        SSRFProtectionError: If URL fails SSRF protection checks
    """
    is_valid, error_msg = validate_url_ssrf(url)
    if not is_valid:
        raise SSRFProtectionError(error_msg)
