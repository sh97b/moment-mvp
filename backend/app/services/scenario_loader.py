"""합성 시나리오 JSON의 위치 결정, 파싱, 검증과 시간순 정렬을 담당한다."""

import json
from math import isfinite
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from backend.app.models.replay import SafetyFeatures
from backend.app.models.scenario import ScenarioSummary
from backend.app.services.gps_feature_engineering import GpsPoint, calculate_gps_features


class ScenarioNotFoundError(Exception):
    pass


class ScenarioUnavailableError(Exception):
    pass


class ScenarioDataError(Exception):
    pass


class RawGpsPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    lat: float
    lng: float

    @field_validator("timestamp")
    @classmethod
    def timestamp_has_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @field_validator("lat")
    @classmethod
    def latitude_in_range(cls, value: float) -> float:
        if not isfinite(value) or not -90 <= value <= 90:
            raise ValueError("invalid latitude")
        return value

    @field_validator("lng")
    @classmethod
    def longitude_in_range(cls, value: float) -> float:
        if not isfinite(value) or not -180 <= value <= 180:
            raise ValueError("invalid longitude")
        return value


class RawFrame(RawGpsPoint):
    features: SafetyFeatures
    anomaly_score: Any = None
    is_anomaly: Any = None


# 공개 scenario ID와 파일명을 한곳에서 관리해 라우터가 경로를 알지 않게 한다.
SCENARIOS: dict[str, tuple[str, str, str]] = {
    "normal": ("normal.json", "정상 이동", "평소 경로를 따라 목적지에 다녀옵니다."),
    "temporary_return": (
        "temporary_return.json",
        "일시 이탈 후 복귀",
        "경로를 잠시 벗어나지만 안내 후 정상 경로로 복귀합니다.",
    ),
    "persistent_anomaly": (
        "persistent_anomaly.json",
        "이상 이동 지속",
        "반복 이동과 방향 전환이 지속되고 집과의 거리가 증가합니다.",
    ),
    "gps_normal": (
        "gps_replay/normal.json",
        "GPS 정상 이동",
        "GPS 좌표에서 계산한 정상 이동 시나리오입니다.",
    ),
    "gps_temporary_return": (
        "gps_replay/temporary_return.json",
        "GPS 일시 이탈 후 복귀",
        "GPS 좌표에서 계산한 일시 이탈 후 복귀 시나리오입니다.",
    ),
    "gps_persistent_anomaly": (
        "gps_replay/persistent_anomaly.json",
        "GPS 이상 이동 지속",
        "GPS 좌표에서 계산한 이상 이동 지속 시나리오입니다.",
    ),
}
GPS_SCENARIO_IDS = frozenset(
    {"gps_normal", "gps_temporary_return", "gps_persistent_anomaly"}
)


class ScenarioLoader:
    """실제 합성 데이터를 우선하고 없을 때만 내장 데모 fixture를 사용한다."""

    def __init__(self, data_dir: Path | None = None, fallback_dir: Path | None = None):
        repository_root = Path(__file__).resolve().parents[3]
        self.data_dir = data_dir or repository_root / "data" / "synthetic"
        self.fallback_dir = fallback_dir or Path(__file__).resolve().parents[1] / "fixtures"

    def list_scenarios(self) -> list[ScenarioSummary]:
        return [
            ScenarioSummary(id=scenario_id, name=metadata[1], description=metadata[2])
            for scenario_id, metadata in SCENARIOS.items()
            if self._resolve_path(metadata[0]) is not None
        ]

    def load(self, scenario_id: str) -> list[RawFrame]:
        """시나리오를 검증한 뒤 timestamp 오름차순으로 반환한다."""
        metadata = SCENARIOS.get(scenario_id)
        if metadata is None:
            raise ScenarioNotFoundError
        path = self._resolve_path(metadata[0])
        if path is None:
            raise ScenarioUnavailableError("Scenario data is temporarily unavailable")
        try:
            payload = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"invalid JSON constant: {value}")
                ),
            )
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            raise ScenarioDataError("Scenario data is not valid JSON") from exc
        except OSError as exc:
            raise ScenarioUnavailableError("Scenario data is temporarily unavailable") from exc

        frames_payload = payload.get("frames") if isinstance(payload, dict) else payload
        if not isinstance(frames_payload, list):
            raise ScenarioDataError("Scenario frames must be an array")
        try:
            frames = [RawFrame.model_validate(frame) for frame in frames_payload]
            if scenario_id in GPS_SCENARIO_IDS:
                frames = self._with_calculated_gps_features(payload, frames)
        except (ValidationError, ValueError) as exc:
            raise ScenarioDataError("Scenario frame validation failed") from exc
        return sorted(frames, key=lambda frame: frame.timestamp)

    @staticmethod
    def _with_calculated_gps_features(
        payload: Any,
        frames: list[RawFrame],
    ) -> list[RawFrame]:
        history_payload = payload.get("history") if isinstance(payload, dict) else None
        if not isinstance(history_payload, list) or len(history_payload) < 15:
            raise ValueError("GPS scenario requires at least 15 history points")

        history = [RawGpsPoint.model_validate(point) for point in history_payload]
        source_points = [*history, *frames]
        calculated = calculate_gps_features(
            [
                GpsPoint(timestamp=point.timestamp, lat=point.lat, lng=point.lng)
                for point in source_points
            ]
        )[len(history):]

        return [
            frame.model_copy(
                update={
                    "features": SafetyFeatures.model_validate(
                        {
                            **frame.features.model_dump(),
                            **feature.as_dict(),
                        }
                    )
                }
            )
            for frame, feature in zip(frames, calculated, strict=True)
        ]

    def _resolve_path(self, filename: str) -> Path | None:
        # 데이터팀 파일이 추가되면 백엔드 수정 없이 fixture보다 먼저 선택된다.
        primary = self.data_dir / filename
        if primary.is_file():
            return primary
        fallback = self.fallback_dir / filename
        return fallback if fallback.is_file() else None
