"""Human-reviewed cross-channel publication draft adapter."""

from .core import (
    CHANNEL_POLICY,
    CONTENT_BUDGET,
    FACT_PRIORITY,
    OVERFLOW_STRATEGY,
    PostAdapterError,
    build_bundle,
    normalize_source,
    register_adapter,
)

__all__ = [
    "CHANNEL_POLICY",
    "CONTENT_BUDGET",
    "FACT_PRIORITY",
    "OVERFLOW_STRATEGY",
    "PostAdapterError",
    "build_bundle",
    "normalize_source",
    "register_adapter",
]
