"""Broadcast addresses for discovery.

Vendored change: upstream used netifaces, which has no wheels for Python 3.13
and fails to build. We configure devices by IP, so a plain global broadcast is
enough.
"""


def get_broadcasts(excluded=None):
    """Return broadcast addresses to probe."""
    return ["255.255.255.255"]


def get_interfaces(excluded=None):
    """Unused; kept for API compatibility."""
    return []


def get_networks(excluded=None):
    """Unused; kept for API compatibility."""
    return []
