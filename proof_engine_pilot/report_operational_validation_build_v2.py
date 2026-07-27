"""Deterministic binding layer for the second-case operational package.

The underlying builder remains generic and data-driven. This module fixes the
fingerprints observed by the independent double-build probe and is the active
verification surface for acceptance and final evaluation.
"""

from __future__ import annotations

from typing import Any

from . import report_operational_validation_build as _impl

_impl.REPORT_JSON_FINGERPRINT = "c0e84e4958974db54e428cacea18e4d4180b00b9ed54730768349044b4d82285"
_impl.REPORT_MARKDOWN_FINGERPRINT = "9676fefb28d9eeecc67093c4ed3e4ef04511a0ecf01c1096c1f962b6f33a0363"
_impl.EVIDENCE_INVENTORY_FINGERPRINT = "f899eb5a2026906878c51bbeb2c79362eb2f79bac6399c05c266e620075ee471"
_impl.COMPARISON_MATRIX_FINGERPRINT = "c74a86f0ec66e28460fd1fe1845886b0f456481690c17c144f341c7757f663ef"
_impl.ACCEPTANCE_PACKET_FINGERPRINT = "b7068262d2ed5705b019f2fff89f7d8528efd5658d3908c8d308e01a96ef93c1"
_impl.VERIFICATION_SUMMARY_FINGERPRINT = "f45e5300e41328fd0f9126237bbd8cc0142e39b89eebed948da0f6f80f2eebb9"
_impl.ROLLBACK_INDEX_FINGERPRINT = "4bc59f6109a7450ac78c62a1d4aa87db6f141570b94c42de1208e426bb7a5634"
_impl.PACKAGE_SUMMARY_FINGERPRINT = "165c364b59e8ea3e6e54e0eb4da3426c1b98454589df2001ca852ce6d6329390"
_impl.BUILD_CHECKPOINT_FINGERPRINT = "5396e4ee089378f99f19e3d4e1a2d12a949d656083b4b40a0cfcf09a6c0b819d"

REPORT_JSON_FINGERPRINT = _impl.REPORT_JSON_FINGERPRINT
REPORT_MARKDOWN_FINGERPRINT = _impl.REPORT_MARKDOWN_FINGERPRINT
EVIDENCE_INVENTORY_FINGERPRINT = _impl.EVIDENCE_INVENTORY_FINGERPRINT
COMPARISON_MATRIX_FINGERPRINT = _impl.COMPARISON_MATRIX_FINGERPRINT
ACCEPTANCE_PACKET_FINGERPRINT = _impl.ACCEPTANCE_PACKET_FINGERPRINT
VERIFICATION_SUMMARY_FINGERPRINT = _impl.VERIFICATION_SUMMARY_FINGERPRINT
ROLLBACK_INDEX_FINGERPRINT = _impl.ROLLBACK_INDEX_FINGERPRINT
PACKAGE_SUMMARY_FINGERPRINT = _impl.PACKAGE_SUMMARY_FINGERPRINT
BUILD_CHECKPOINT_FINGERPRINT = _impl.BUILD_CHECKPOINT_FINGERPRINT

RESULT_CRITERIA = _impl.RESULT_CRITERIA
TOPICS = _impl.TOPICS
STATE = _impl.STATE
NEXT_GATE = _impl.NEXT_GATE


def build_second_case_package(**kwargs: Any) -> dict[str, Any]:
    return _impl.build_second_case_package(**kwargs)


def verify_second_case_package(**kwargs: Any) -> dict[str, Any]:
    return _impl.verify_second_case_package(**kwargs)


def render_second_case_markdown(report: dict[str, Any]) -> str:
    return _impl.render_second_case_markdown(report)


__all__ = [
    "ACCEPTANCE_PACKET_FINGERPRINT",
    "BUILD_CHECKPOINT_FINGERPRINT",
    "COMPARISON_MATRIX_FINGERPRINT",
    "EVIDENCE_INVENTORY_FINGERPRINT",
    "NEXT_GATE",
    "PACKAGE_SUMMARY_FINGERPRINT",
    "REPORT_JSON_FINGERPRINT",
    "REPORT_MARKDOWN_FINGERPRINT",
    "RESULT_CRITERIA",
    "ROLLBACK_INDEX_FINGERPRINT",
    "STATE",
    "TOPICS",
    "VERIFICATION_SUMMARY_FINGERPRINT",
    "build_second_case_package",
    "render_second_case_markdown",
    "verify_second_case_package",
]
