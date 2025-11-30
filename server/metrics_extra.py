"""Lightweight metrics extension used at app startup.

This module exposes a single function `init(registry)` which registers
optional application-specific Prometheus metrics. Keep this minimal so
tests and import-time execution succeed.
"""
from prometheus_client import Gauge

def init(registry):
    try:
        # Example custom metric: application ready/up flag
        app_up = Gauge("otp_app_up", "Application ready/up", registry=registry)
        app_up.set(1)
    except Exception:
        # Don't raise during startup; metrics are optional
        pass

    # Return nothing; callers only need the side-effect of registration
    return None
