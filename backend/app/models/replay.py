"""Replay API의 내부 입력 모델과 공개 응답 계약을 정의한다."""

from datetime import datetime
from math import isfinite

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not isfinite(value)
    if isinstance(value, dict):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_non_finite(item) for item in value)
    return False


class Alert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    message: str


class SafetyFeatures(BaseModel):
    """Safety Loop 계산용 내부 feature로, 향후 모델 feature 확장을 허용한다."""

    model_config = ConfigDict(extra="allow")

    turn_count: int = 0
    revisit_count: int = 0
    home_distance_m: float = 0.0
    home_distance_delta_m: float = 0.0
    distance_from_route_m: float = 0.0
    deviation_m: float | None = None
    stationary_duration_sec: float = 0.0
    heading_change_deg: float = 0.0
    elapsed_sec: float = 0.0
    returned_to_route: bool = False

    @field_validator("home_distance_m", "home_distance_delta_m", "distance_from_route_m", "deviation_m", "stationary_duration_sec", "heading_change_deg", "elapsed_sec")
    @classmethod
    def finite_numbers(cls, value: float | None) -> float | None:
        if value is not None and not isfinite(value):
            raise ValueError("feature values must be finite")
        return value

    @model_validator(mode="after")
    def finite_extra_values(self) -> "SafetyFeatures":
        if _contains_non_finite(self.__pydantic_extra__ or {}):
            raise ValueError("feature values must be finite")
        return self


class FrameFeatures(BaseModel):
    """docs/api-contract.md에 고정된 공개 feature만 노출한다."""

    model_config = ConfigDict(extra="forbid")

    turn_count: int = 0
    revisit_count: int = 0
    home_distance_m: float = 0.0
    home_distance_delta_m: float = 0.0


class ReplayFrame(BaseModel):
    """프론트엔드가 한 시점씩 재생하는 검증 완료 frame."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    lat: float
    lng: float
    features: FrameFeatures
    anomaly_score: float
    risk_level: int
    reasons: list[str]
    elderly_alert: Alert | None
    guardian_alert: Alert | None

    @field_validator("timestamp")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @field_validator("lat")
    @classmethod
    def valid_latitude(cls, value: float) -> float:
        if not isfinite(value) or not -90 <= value <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("lng")
    @classmethod
    def valid_longitude(cls, value: float) -> float:
        if not isfinite(value) or not -180 <= value <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return value

    @field_validator("anomaly_score")
    @classmethod
    def valid_score(cls, value: float) -> float:
        if not isfinite(value) or not 0 <= value <= 1:
            raise ValueError("anomaly_score must be between 0 and 1")
        return value

    @field_validator("risk_level")
    @classmethod
    def valid_risk_level(cls, value: int) -> int:
        if not 0 <= value <= 3:
            raise ValueError("risk_level must be between 0 and 3")
        return value


class ReplayResponse(BaseModel):
    """프론트 타이머가 한 번에 받는 전체 시나리오 응답."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    interval_ms: int = 1000
    frames: list[ReplayFrame]
