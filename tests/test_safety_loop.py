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