"""Human-reviewed cross-channel publication draft adapter."""

from .core import (
    PostAdapterError,
    build_bundle,
    normalize_source,
    register_adapter,
)

__all__ = [
    "PostAdapterError",
    "build_bundle",
    "normalize_source",
    "register_adapter",
]
