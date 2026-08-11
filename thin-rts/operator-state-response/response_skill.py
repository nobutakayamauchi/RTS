#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from effect_catalog import estimate_performance_impact, PerformanceImpact
from environment_context import (
    EnvironmentConsent,
    EnvironmentObservation,
    minimized_environment_record,
)
from medical_guard import evaluate_medical_guard, MedicalGuardResult
from state_model import OperatorStateInput, FatigueEstimate, estimate_fatigue
from vitals_model import Vitals, personal_vital_deviation


@dataclass(frozen=True)
class ResponseContext:
    eta_return_minutes: int | None = None
    eta_late_after_minutes: int | None = None
    rework_minutes: int | None = None
    decision_review_level: str | None = None
    heat_exposure: bool = False
    cannot_drink: bool = False
    vitals: Vitals | None = None
    vitals_baseline: Mapping[str, Iterable[float]] = field(default_factory=dict)
    sleep_environment_kind: str | None = None
    environment_consent: EnvironmentConsent = field(default_factory=EnvironmentConsent)
    environment: EnvironmentObservation | None = None


@dataclass(frozen=True)
class SkillResult:
    text: str
    fatigue: FatigueEstimate
    performance: PerformanceImpact
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
    if not state.bad_status_assessed and not state.bad_status:
        questions.append("今あるバッドステータスは？（なければ『なし』。頭痛、吐き気、めまい、発熱感、倒れた等）")

    consent = ctx.environment_consent.validated()
    if (
        (ctx.sleep_environment_kind or "").strip().lower() == "vehicle"
        and consent.weather_mode == "NOT_ASKED"
        and len(questions) < 3
    ):
        questions.append(
            "車中泊の睡眠環境補正に、現在地を天気取得だけへ一時利用していい？"
            "（既定ではGPSを保存しない）"
        )
    if (
        (ctx.sleep_environment_kind or "").strip().lower() == "vehicle"
        and consent.noise_mode == "NOT_ASKED"
        and len(questions) < 3
    ):
        questions.append(
            "周囲音も取る？（任意。許可時も既定は音声保存なし・dB等の派生値だけ）"
        )
    if ctx.vitals is None and len(questions) < 3:
        questions.append("測っているバイタルがあれば数値も残す？（任意。なくても進める）")
    return tuple(questions[:3])


def _environment_line(ctx: ResponseContext) -> str | None:
    if ctx.environment is None:
        return None
    obs = ctx.environment.validated()
    parts: list[str] = []
    if obs.outdoor_temp_c is not None:
        parts.append(f"OUT {obs.outdoor_temp_c:.1f}C")
    if obs.outdoor_relative_humidity_pct is not None:
        parts.append(f"RH {obs.outdoor_relative_humidity_pct:.0f}%")
    if obs.cabin_temp_c is not None:
        parts.append(f"CABIN {obs.cabin_temp_c:.1f}C")
    if obs.cabin_relative_humidity_pct is not None:
        parts.append(f"CABIN_RH {obs.cabin_relative_humidity_pct:.0f}%")
    consent = ctx.environment_consent.validated()
    if consent.noise_mode == "DERIVED_DB_ONLY" and obs.noise_laeq_db is not None:
        parts.append(f"NOISE_LAEQ {obs.noise_laeq_db:.1f}dB")
    if obs.subjective_noise_0_10 is not None:
        parts.append(f"NOISE_SUBJ {obs.subjective_noise_0_10:.1f}/10")
    if not parts:
        return None
    return "SLEEP_ENV " + " / ".join(parts)


def evaluate_response(state: OperatorStateInput, ctx: ResponseContext) -> SkillResult:
    fatigue = estimate_fatigue(state)
    performance = estimate_performance_impact(
        sleep_hours_24h=state.sleep_hours_24h,
        continuous_awake_hours=state.continuous_awake_hours,
        sleep_restriction_nights=state.sleep_restriction_nights,
    )
    medical = evaluate_medical_guard(
        state.bad_status,
        heat_exposure=ctx.heat_exposure,
        cannot_drink=ctx.cannot_drink,
    )
    vital_z = personal_vital_deviation(ctx.vitals, ctx.vitals_baseline)
    questions = _questions(state, medical, ctx)

    if ctx.eta_return_minutes is None:
        return_text = "RETURN ?"
    else:
        return_text = f"RETURN {ctx.eta_return_minutes}m"
    if ctx.eta_late_after_minutes is not None:
        return_text += f" / LATE {ctx.eta_late_after_minutes}m"
    if ctx.rework_minutes is not None:
        return_text += f" / REWORK +{ctx.rework_minutes}m"

    axis = performance.axes
    lines = [
        return_text,
        f"FATIGUE_EST {fatigue.operational_fatigue_100:.1f}/100 {fatigue.band} ({fatigue.confidence}, cov={fatigue.evidence_coverage:.0%})",
        "PERF_PRIOR "
        f"J:{axis['judgment'].grade} "
        f"R:{axis['reaction'].grade} "
        f"A:{axis['accuracy'].grade} "
        f"O:{axis['operation'].grade}",
    ]
    if performance.comparative_references:
        lines.append("COMPARATOR " + " | ".join(performance.comparative_references))
    env_line = _environment_line(ctx)
    if env_line:
        lines.append(env_line)
    if state.recovery_events:
        lines.append("RECOVERY " + ", ".join(state.recovery_events))
    if state.bad_status:
        lines.append("BAD " + ", ".join(state.bad_status))
    elif state.bad_status_assessed:
        lines.append("BAD none_reported")
    if any(v is not None and v > 1.5 for v in fatigue.behavior_z.values()):
        abnormal = [f"{k} z={v:.1f}" for k, v in fatigue.behavior_z.items() if v is not None and v > 1.5]
        lines.append("BEHAVIOR ↑ " + ", ".join(abnormal))
    elif "behavior_uncalibrated" in fatigue.notes:
        lines.append("BEHAVIOR uncalibrated")

    vital_hits = [f"{k} z={v:+.1f}" for k, v in vital_z.items() if v is not None and abs(v) > 1.5]
    if vital_hits:
        lines.append("VITAL_BASELINE Δ " + ", ".join(vital_hits))
    elif ctx.vitals is not None and not any(v is not None for v in vital_z.values()):
        lines.append("VITAL_BASELINE uncalibrated")

    if ctx.decision_review_level:
        lines.append(f"DECISION_REVIEW {ctx.decision_review_level.upper()}")
    if medical.level != "NONE":
        lines.append(f"MEDICAL {medical.level}: {medical.action}")
    else:
        lines.append("MEDICAL no reported red flag")
    if questions:
        lines.append("ASK " + " / ".join(questions))

    environment_record = minimized_environment_record(ctx.environment, ctx.environment_consent)
    log_record = {
        "schema": "operator-state-response/v0",
        "sleep_hours_24h": state.sleep_hours_24h,
        "continuous_awake_hours": state.continuous_awake_hours,
        "sleep_restriction_nights": state.sleep_restriction_nights,
        "sleep_environment_kind": ctx.sleep_environment_kind,
        "environment_consent": {
            "weather_mode": ctx.environment_consent.validated().weather_mode,
            "noise_mode": ctx.environment_consent.validated().noise_mode,
        },
        "environment": environment_record,
        "subjective_fatigue_0_10": state.subjective_fatigue_0_10,
        "subjective_recovery_0_10": state.subjective_recovery_0_10,
        "recovery_events": list(state.recovery_events),
        "bad_status": list(state.bad_status),
        "bad_status_assessed": state.bad_status_assessed or bool(state.bad_status),
        "fatigue_estimate_100": fatigue.operational_fatigue_100,
        "fatigue_band": fatigue.band,
        "fatigue_confidence": fatigue.confidence,
        "fatigue_coverage": fatigue.evidence_coverage,
        "performance_prior": {key: value.grade for key, value in performance.axes.items()},
        "performance_evidence_ids": list(performance.matched_profiles),
        "performance_comparators": list(performance.comparative_references),
        "behavior_z": fatigue.behavior_z,
        "vital_z": vital_z,
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
        performance=performance,
        medical=medical,
        questions=questions,
        log_record=log_record,
    )
