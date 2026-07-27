"""Compatibility entry point for the evidence report template.

The implementation lives in ``report_template_v2`` because it must combine
verified campaign metadata with generated-run candidate fingerprints. Keeping
this module as the stable import surface avoids breaking the CLI and tests.
"""

from .report_template_v2 import (
    CHECKPOINT_PATH,
    CONTRACT_PATH,
    MANIFEST_PATH,
    REQUIRED_ACHIEVEMENT_FIELDS,
    REQUIRED_SECTIONS,
    build_demonstration_pack,
    build_template,
    render_demonstration_markdown,
    verify_report_template,
    verify_template_contract,
    verify_template_manifest,
)

__all__ = [
    "CHECKPOINT_PATH",
    "CONTRACT_PATH",
    "MANIFEST_PATH",
    "REQUIRED_ACHIEVEMENT_FIELDS",
    "REQUIRED_SECTIONS",
    "build_demonstration_pack",
    "build_template",
    "render_demonstration_markdown",
    "verify_report_template",
    "verify_template_contract",
    "verify_template_manifest",
]
