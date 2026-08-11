#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from medical_guard import evaluate_medical_guard, MedicalGuardResult
from state_model import OperatorStateInput, FatigueEstimate, estimate_fatigue


@dataclass(frozen=True)
class ResponseContext:
    eta_return_minutes: int | None = None
    eta_late_after_minutes: int | None = None
    rework_minutes: int | None = None
    decision_review_level: str | None = None
    heat_exposure: bool = False
    cannot_drink: bool = False
    vitals_present: bool = False


@dataclass(frozen=True)
class SkillResult:
    text: str
    fatigue: FatigueEstimate
    medical: MedicalGuardResult
    questions: tuple[str, ...]
    log_record: dict[str, object]


def _questions(state: OperatorStateInput, medical: MedicalGuardResult, ctx: ResponseContext) -> tuple[str, ...]:
    if medical.level == "EMERGENCY":
        return ()
    questions: list[str] = []
    if state.sleep_hours_24h is None:
        questions.append("直近24時間の睡眠は合計何時間くらい？")
    if state.subjective_recovery_0_10 is None:
        questions.append("仮眠・睡眠・食事・水分・休憩のあと、回復感は0〜10でどれくらい？")
    if not state.bad_status:
        questions.append("今あるバッドステータスは？（頭痛、吐き気、めまい、発熱感、倒れた等）")
    if ctx.vitals_present is False and len(questions) < 3:
        questions.append("測っているバイタルがあれば数値も残す？（任意。なくても進める）")
    return tuple(questions[:3])


def evaluate_response(state: OperatorStateInput, ctx: ResponseContext) -> SkillResult:
    fatigue = estimate_fatigue(state)
    medical = evaluate_medical_guard(
        state.bad_status,
        heat_exposure=ctx.heat_exposure,
        cannot_drink=ctx.cannot_drink,
    )
    questions = _questions(state, medical, ctx)

    if ctx.eta_return_minutes is None:
        return_text = "RETURN ?"
    else:
        return_text = f"RETURN {ctx.eta_return_minutes}m"
    if ctx.eta_late_after_minutes is not None:
        return_text += f" / LATE {ctx.eta_late_after_minutes}m"
    if ctx.rework_minutes is not None:
        return_text += f" / REWORK +{ctx.rework_minutes}m"

    lines = [
        return_text,
        f"FATIGUE_EST {fatigue.operational_fatigue_100:.1f}/100 {fatigue.band} ({fatigue.confidence}, cov={fatigue.evidence_coverage:.0%})",
    ]
    if state.recovery_events:
        lines.append("RECOVERY " + ", ".join(state.recovery_events))
    if state.bad_status:
        lines.append("BAD " + ", ".join(state.bad_status))
    if any(v is not None and v > 1.5 for v in fatigue.behavior_z.values()):
        abnormal = [f"{k} z={v:.1f}" for k, v in fatigue.behavior_z.items() if v is not None and v > 1.5]
        lines.append("BEHAVIOR ↑ " + ", ".join(abnormal))
    elif "behavior_uncalibrated" in fatigue.notes:
        lines.append("BEHAVIOR uncalibrated")

    if ctx.decision_review_level:
        lines.append(f"DECISION_REVIEW {ctx.decision_review_level.upper()}")
    if medical.level != "NONE":
        lines.append(f"MEDICAL {medical.level}: {medical.action}")
    else:
        lines.append("MEDICAL no reported red flag")
    if questions:
        lines.append("ASK " + " / ".join(questions))

    log_record = {
        "schema": "operator-state-response/v0",
        "sleep_hours_24h": state.sleep_hours_24h,
        "subjective_fatigue_0_10": state.subjective_fatigue_0_10,
        "subjective_recovery_0_10": state.subjective_recovery_0_10,
        "recovery_events": list(state.recovery_events),
        "bad_status": list(state.bad_status),
        "fatigue_estimate_100": fatigue.operational_fatigue_100,
        "fatigue_band": fatigue.band,
        "fatigue_confidence": fatigue.confidence,
        "fatigue_coverage": fatigue.evidence_coverage,
        "behavior_z": fatigue.behavior_z,
        "eta_return_minutes": ctx.eta_return_minutes,
        "eta_late_after_minutes": ctx.eta_late_after_minutes,
        "rework_minutes": ctx.rework_minutes,
        "decision_review_level": ctx.decision_review_level,
        "medical_level": medical.level,
        "medical_flags": list(medical.flags),
        "medical_semantics": medical.semantics,
    }
    return SkillResult(
        text="\n".join(lines),
        fatigue=fatigue,
        medical=medical,
        questions=questions,
        log_record=log_record,
    )
