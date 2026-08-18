from backend.app.ai.predictor import predict_anomaly
from backend.app.ai.safety_loop import SafetyLoop


def test_safety_loop_level_transition():

    safety_loop = SafetyLoop()

    sequence = [
        (3, 0),
        (6, 0),
        (6, 0),
        (7, 0),
        (7, 0),
        (8, 1),
        (8, 2),
        (9, 3),
        (9, 4),
        (3, 0),
        (3, 0),
        (3, 0),
    ]

    expected_levels = [
        0,
        1,
        1,
        1,
        2,
        2,
        2,
        3,
        3,
        2,
        1,
        0,
    ]

    actual_levels = []

    for turn, revisit in sequence:

        prediction = predict_anomaly(
            turn_10min=turn,
            revisit_15min=revisit,
        )

        result = safety_loop.update(
            prediction
        )

        actual_levels.append(
            result["current_level"]
        )

    assert actual_levels == expected_levels


from pathlib import Path

import pandas as pd




def test_s_route_003_full_transition():
    root_dir = Path(__file__).resolve().parents[1]

    scenario_path = (
        root_dir
        / "data"
        / "synthetic"
        / "scenario_data.csv"
    )

    df = pd.read_csv(scenario_path)

    route_df = (
        df[
            df["route_id"] == "S_ROUTE_003"
        ]
        .sort_values("timestamp")
        .copy()
    )

    assert not route_df.empty

    safety_loop = SafetyLoop()

    levels_by_time = {}

    for _, row in route_df.iterrows():
        prediction = predict_anomaly(
            turn_10min=int(row["turn_10min"]),
            revisit_15min=int(row["revisit_15min"]),
        )

        result = safety_loop.update(prediction)

        levels_by_time[row["timestamp"]] = (
            result["current_level"]
        )

    assert levels_by_time["09:05"] == 1
    assert levels_by_time["09:06"] == 2
    assert levels_by_time["09:09"] == 3

    # 위험 진입 후 마지막까지 위험 유지
    assert levels_by_time["09:20"] == 3