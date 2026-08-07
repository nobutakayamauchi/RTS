"""RTS runtime evidence correlation gate."""

from .core import CorrelationError, correlate_candidates, validate_correlation_result

__all__ = ["CorrelationError", "correlate_candidates", "validate_correlation_result"]
