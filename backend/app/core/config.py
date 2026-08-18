"""Safety Loop에서 공통으로 사용하는 조정 가능한 데모 임계값."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SafetyThresholds:
    """합성 데이터 평가로 조정할 데모 기본값이며 의료적 기준이 아니다."""

    route_deviation_m: float = 80.0
    recovered_route_m: float = 40.0
    stationary_duration_sec: float = 300.0
    heading_change_deg: float = 100.0
    turn_count: int = 4
    revisit_count: int = 2
    anomaly_score: float = 0.65
    severe_anomaly_score: float = 0.85
    recovery_frames: int = 2
    level_two_frames: int = 2
    level_three_frames: int = 3


SAFETY_THRESHOLDS = SafetyThresholds()
