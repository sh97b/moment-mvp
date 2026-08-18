import json
from math import isfinite
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from backend.app.models.replay import SafetyFeatures
from backend.app.models.scenario import ScenarioSummary


class ScenarioNotFoundError(Exception):
    pass


class ScenarioUnavailableError(Exception):
    pass


class ScenarioDataError(Exception):
    pass


class RawFrame(BaseModel):
    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    lat: float
    lng: float
    features: SafetyFeatures
    anomaly_score: Any = None
    is_anomaly: Any = None

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
}


class ScenarioLoader:
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
        except ValidationError as exc:
            raise ScenarioDataError("Scenario frame validation failed") from exc
        return sorted(frames, key=lambda frame: frame.timestamp)

    def _resolve_path(self, filename: str) -> Path | None:
        primary = self.data_dir / filename
        if primary.is_file():
            return primary
        fallback = self.fallback_dir / filename
        return fallback if fallback.is_file() else None
