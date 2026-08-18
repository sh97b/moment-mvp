from dataclasses import dataclass
from math import isfinite
from typing import Any

from backend.app.core.config import SAFETY_THRESHOLDS, SafetyThresholds


@dataclass(frozen=True)
class SafetyState:
    risk_level: int = 0
    abnormal_frames: int = 0
    recovery_frames: int = 0


@dataclass(frozen=True)
class SafetyDecision:
    state: SafetyState
    anomaly_score: float
    reasons: list[str]


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if isfinite(number) else default


def _valid_model_score(value: Any) -> float | None:
    score = _number(value, default=-1.0)
    return score if 0.0 <= score <= 1.0 else None


def evaluate_safety(
    features: dict[str, Any],
    previous: SafetyState = SafetyState(),
    *,
    model_score: Any = None,
    model_is_anomaly: Any = None,
    thresholds: SafetyThresholds = SAFETY_THRESHOLDS,
) -> SafetyDecision:
    """Return one deterministic transition without retaining cross-request state."""
    deviation_value = features.get("deviation_m")
    if deviation_value is None:
        deviation_value = features.get("distance_from_route_m", 0.0)
    deviation = _number(deviation_value)
    stationary = _number(features.get("stationary_duration_sec"))
    heading_change = _number(features.get("heading_change_deg"))
    turns = _number(features.get("turn_count"))
    revisits = _number(features.get("revisit_count"))
    home_delta = _number(features.get("home_distance_delta_m"))
    returned = features.get("returned_to_route") is True

    score = _valid_model_score(model_score)
    model_signal = score is not None and (
        model_is_anomaly is True or score >= thresholds.anomaly_score
    )

    reasons: list[str] = []
    if deviation >= thresholds.route_deviation_m:
        reasons.append("평소 이동 경로에서 벗어난 상태가 감지되었습니다.")
    if stationary >= thresholds.stationary_duration_sec:
        reasons.append("한 구간에 머문 시간이 평소보다 깁니다.")
    if turns >= thresholds.turn_count or heading_change >= thresholds.heading_change_deg:
        reasons.append("최근 구간의 방향 전환이 평소보다 많습니다.")
    if revisits >= thresholds.revisit_count:
        reasons.append("같은 구간을 반복해서 이동하는 징후가 있습니다.")
    if model_signal:
        reasons.append("이동 패턴의 이상 점수가 기준을 넘었습니다.")

    # When model output is absent or invalid, derive a bounded UI score from rules.
    if score is None:
        rule_weights = (
            (0.35 if deviation >= thresholds.route_deviation_m else 0.0)
            + (0.25 if stationary >= thresholds.stationary_duration_sec else 0.0)
            + (0.2 if turns >= thresholds.turn_count or heading_change >= thresholds.heading_change_deg else 0.0)
            + (0.2 if revisits >= thresholds.revisit_count else 0.0)
        )
        score = min(1.0, max(0.0, rule_weights))

    abnormal_count = len(reasons)
    recovering = (
        returned
        or (deviation < thresholds.recovered_route_m and home_delta < 0)
    ) and not model_signal and abnormal_count == 0

    if recovering and previous.risk_level > 0:
        recovery_frames = previous.recovery_frames + 1
        risk_level = previous.risk_level
        if recovery_frames >= thresholds.recovery_frames:
            risk_level = max(0, previous.risk_level - 1)
            recovery_frames = 0
        state = SafetyState(risk_level, 0, recovery_frames)
        return SafetyDecision(state, score, ["평소 경로로 복귀하는 흐름이 확인되었습니다."])

    if abnormal_count:
        streak = previous.abnormal_frames + 1
        if previous.risk_level == 0:
            level = 1
        elif previous.risk_level == 1 and streak >= thresholds.level_two_frames and abnormal_count >= 2:
            level = 2
        elif (
            previous.risk_level == 2
            and streak >= thresholds.level_three_frames
            and abnormal_count >= 3
            and home_delta > 0
        ):
            level = 3
        else:
            level = previous.risk_level
        return SafetyDecision(SafetyState(level, streak, 0), score, reasons)

    # Isolated coordinate noise neither raises nor abruptly drops the level.
    return SafetyDecision(SafetyState(previous.risk_level, 0, 0), score, [])
