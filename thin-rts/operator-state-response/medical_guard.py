#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MedicalGuardResult:
    level: str
    flags: tuple[str, ...]
    action: str
    semantics: str = "SAFETY_TRIAGE_NOT_DIAGNOSIS"


EMERGENCY_FLAGS = {
    "unconscious",
    "altered_consciousness",
    "seizure",
    "sudden_severe_headache",
    "breathing_difficulty",
    "chest_pressure",
    "one_sided_weakness",
    "speech_difficulty",
    "sudden_unable_to_stand",
}

PROMPT_TRIAGE_FLAGS = {
    "fainted_or_collapsed",
    "persistent_vomiting",
    "rapid_worsening",
}

HEAT_SYMPTOMS = {
    "dizziness",
    "heavy_sweating",
    "headache",
    "nausea",
    "weakness",
    "muscle_cramp",
}


def evaluate_medical_guard(
    status_tags: Iterable[str],
    *,
    heat_exposure: bool = False,
    cannot_drink: bool = False,
) -> MedicalGuardResult:
    tags = {str(tag).strip().lower() for tag in status_tags if str(tag).strip()}
    emergency = sorted(tags & EMERGENCY_FLAGS)
    if heat_exposure and cannot_drink:
        emergency.append("heat_exposure_and_cannot_drink")
    if emergency:
        return MedicalGuardResult(
            level="EMERGENCY",
            flags=tuple(dict.fromkeys(emergency)),
            action="STOP_WORK_AND_USE_OFFICIAL_EMERGENCY_TRIAGE",
        )

    prompt = sorted(tags & PROMPT_TRIAGE_FLAGS)
    if prompt:
        return MedicalGuardResult(
            level="PROMPT_TRIAGE",
            flags=tuple(prompt),
            action="PAUSE_WORK_AND_USE_OFFICIAL_TRIAGE_OR_MEDICAL_ASSESSMENT",
        )

    heat_hits = sorted(tags & HEAT_SYMPTOMS)
    if heat_exposure and heat_hits:
        return MedicalGuardResult(
            level="HEAT_CAUTION",
            flags=tuple(heat_hits),
            action="PAUSE_COOL_HYDRATE_AND_REASSESS_USING_OFFICIAL_HEAT_GUIDANCE",
        )

    return MedicalGuardResult(
        level="NONE",
        flags=(),
        action="NO_MEDICAL_RED_FLAG_DETECTED_FROM_REPORTED_FIELDS",
    )
