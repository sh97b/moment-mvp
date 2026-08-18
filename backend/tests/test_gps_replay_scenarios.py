import json
from datetime import datetime

import pytest

from backend.app.services.gps_feature_engineering import GpsPoint, calculate_gps_features
from backend.app.services.gps_scenario_generator import (
    HISTORY_MINUTES,
    OUTPUT_DIR,
    build_scenarios,
    evaluate_scenario,
)


@pytest.fixture(scope="module")
def scenarios():
    return build_scenarios()


def test_generated_files_match_deterministic_generator(scenarios) -> None:
    for scenario_id, expected in scenarios.items():
        stored = json.loads((OUTPUT_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))
        assert stored == expected


@pytest.mark.parametrize("scenario_id", ["normal", "temporary_return", "persistent_anomaly"])
def test_features_are_derived_from_one_minute_gps_points(scenarios, scenario_id) -> None:
    scenario = scenarios[scenario_id]
    source_points = scenario["history"] + scenario["frames"]
    points = [
        GpsPoint(
            timestamp=datetime.fromisoformat(item["timestamp"]),
            lat=item["lat"],
            lng=item["lng"],
        )
        for item in source_points
    ]
    assert len(scenario["history"]) == HISTORY_MINUTES
    assert all(
        (points[index].timestamp - points[index - 1].timestamp).total_seconds() == 60
        for index in range(1, len(points))
    )

    calculated = calculate_gps_features(points)[HISTORY_MINUTES:]
    stored = [frame["features"] for frame in scenario["frames"]]
    assert [feature.as_dict() for feature in calculated] == [
        {
            "turn_count": feature["turn_count"],
            "revisit_count": feature["revisit_count"],
        }
        for feature in stored
    ]


def test_normal_scenario_stays_at_level_zero(scenarios) -> None:
    scenario = scenarios["normal"]
    evaluations = evaluate_scenario(scenario)

    assert {(frame["features"]["turn_count"], frame["features"]["revisit_count"]) for frame in scenario["frames"]} == {(0, 0)}
    assert {result["risk_level"] for result in evaluations} == {0}


def test_temporary_return_rises_then_recovers(scenarios) -> None:
    scenario = scenarios["temporary_return"]
    evaluations = evaluate_scenario(scenario)
    risks = [result["risk_level"] for result in evaluations]
    features = [frame["features"] for frame in scenario["frames"]]

    assert max(frame["turn_count"] for frame in features) == 4
    assert max(frame["revisit_count"] for frame in features) == 2
    assert 1 in risks and 2 in risks and 3 not in risks
    assert risks[-1] == 0
    assert features[-1]["turn_count"] == 0
    assert features[-1]["revisit_count"] == 0


def test_persistent_anomaly_reaches_level_three(scenarios) -> None:
    scenario = scenarios["persistent_anomaly"]
    evaluations = evaluate_scenario(scenario)
    risks = [result["risk_level"] for result in evaluations]
    scores = [result["anomaly_score"] for result in evaluations]
    features = [frame["features"] for frame in scenario["frames"]]

    assert max(frame["turn_count"] for frame in features) == 4
    assert max(frame["revisit_count"] for frame in features) == 2
    assert 1 in risks and 2 in risks and risks[-1] == 3
    assert max(scores) >= 0.85
