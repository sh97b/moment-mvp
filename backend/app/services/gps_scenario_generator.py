"""Generate deterministic GPS-derived replay scenarios for validation only."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

from backend.app.ai.predictor import predict_anomaly
from backend.app.services.gps_feature_engineering import GpsPoint, calculate_gps_features
from backend.app.services.safety_loop import SafetyState, evaluate_safety


SEED = 20260818
STEP_DEGREES = 0.0001
HISTORY_MINUTES = 15
REPLAY_START = datetime(2026, 8, 18, 9, 0, tzinfo=timezone(timedelta(hours=9)))
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "gps_replay"


def _normal_offsets() -> list[tuple[int, int]]:
    return [(index, 0) for index in range(15, 40)]


def _temporary_return_offsets() -> list[tuple[int, int]]:
    detour = [
        (15, 0),
        (16, 0),
        (17, 0),
        (18, 0),
        (18, 1),
        (17, 1),
        (17, 0),
        (18, 0),
    ]
    wait_for_windows = [(18, 0)] * 16
    resumed_route = [(19 + index, 0) for index in range(6)]
    return detour + wait_for_windows + resumed_route


def _persistent_anomaly_offsets() -> list[tuple[int, int]]:
    return [
        (15, 0),
        (16, 0),
        (17, 0),
        (18, 0),
        (18, 2),
        (16, 2),
        (19, -1),
        (17, 3),
        (15, 7),
        (13, 11),
        (11, 15),
        (9, 19),
    ]


def _distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    first_lat, first_lng = map(radians, first)
    second_lat, second_lng = map(radians, second)
    latitude_delta = second_lat - first_lat
    longitude_delta = second_lng - first_lng
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(first_lat) * cos(second_lat) * sin(longitude_delta / 2) ** 2
    )
    return 6_371_000 * 2 * atan2(sqrt(value), sqrt(1 - value))


def _point_payload(point: GpsPoint) -> dict[str, Any]:
    return {
        "timestamp": point.timestamp.isoformat(),
        "lat": round(point.lat, 7),
        "lng": round(point.lng, 7),
    }


def _build_scenario(
    scenario_id: str,
    replay_offsets: list[tuple[int, int]],
    origin: tuple[float, float],
    home_offset: tuple[int, int],
) -> dict[str, Any]:
    history_offsets = [(index, 0) for index in range(HISTORY_MINUTES)]
    offsets = history_offsets + replay_offsets
    first_timestamp = REPLAY_START - timedelta(minutes=HISTORY_MINUTES)
    points = [
        GpsPoint(
            timestamp=first_timestamp + timedelta(minutes=index),
            lat=origin[0] + latitude_offset * STEP_DEGREES,
            lng=origin[1] + longitude_offset * STEP_DEGREES,
        )
        for index, (longitude_offset, latitude_offset) in enumerate(offsets)
    ]
    calculated = calculate_gps_features(points)
    history_points = points[:HISTORY_MINUTES]
    replay_points = points[HISTORY_MINUTES:]
    replay_features = calculated[HISTORY_MINUTES:]
    home = (
        origin[0] + home_offset[1] * STEP_DEGREES,
        origin[1] + home_offset[0] * STEP_DEGREES,
    )
    previous_home_distance = _distance_m(
        (history_points[-1].lat, history_points[-1].lng), home
    )
    frames: list[dict[str, Any]] = []

    for point, feature, (_, latitude_offset) in zip(
        replay_points, replay_features, replay_offsets
    ):
        home_distance = _distance_m((point.lat, point.lng), home)
        feature_payload: dict[str, Any] = {
            **feature.as_dict(),
            "home_distance_m": round(home_distance, 3),
            "home_distance_delta_m": round(home_distance - previous_home_distance, 3),
            "returned_to_route": latitude_offset == 0,
        }
        prediction = predict_anomaly(feature_payload)
        frames.append(
            {
                **_point_payload(point),
                "features": feature_payload,
                "anomaly_score": prediction["anomaly_score"],
                "is_anomaly": prediction["is_anomaly"],
            }
        )
        previous_home_distance = home_distance

    return {
        "scenario_id": scenario_id,
        "seed": SEED,
        "history_minutes": HISTORY_MINUTES,
        "history": [_point_payload(point) for point in history_points],
        "frames": frames,
    }


def build_scenarios() -> dict[str, dict[str, Any]]:
    randomizer = random.Random(SEED)
    scenario_specs = {
        "normal": (_normal_offsets(), (0, 0)),
        "temporary_return": (_temporary_return_offsets(), (0, 0)),
        "persistent_anomaly": (_persistent_anomaly_offsets(), (30, 0)),
    }
    scenarios: dict[str, dict[str, Any]] = {}
    for scenario_id, (offsets, home_offset) in scenario_specs.items():
        origin = (
            37.55 + randomizer.uniform(-0.001, 0.001),
            126.95 + randomizer.uniform(-0.001, 0.001),
        )
        scenarios[scenario_id] = _build_scenario(
            scenario_id, offsets, origin, home_offset
        )
    return scenarios


def evaluate_scenario(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    state = SafetyState()
    evaluations: list[dict[str, Any]] = []
    for frame in scenario["frames"]:
        prediction = predict_anomaly(frame["features"])
        decision = evaluate_safety(
            frame["features"],
            state,
            model_score=prediction["anomaly_score"],
            model_is_anomaly=prediction["is_anomaly"],
        )
        state = decision.state
        evaluations.append(
            {
                "anomaly_score": decision.anomaly_score,
                "risk_level": state.risk_level,
            }
        )
    return evaluations


def generate_files(output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario_id, scenario in build_scenarios().items():
        output_path = output_dir / f"{scenario_id}.json"
        output_path.write_text(
            json.dumps(scenario, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    generate_files()
