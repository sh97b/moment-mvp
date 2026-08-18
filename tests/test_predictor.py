import pytest

from backend.app.ai.predictor import (
    predict_anomaly,
)


@pytest.mark.parametrize(
    "turn,revisit,expected_count",
    [
        (3, 0, 0),
        (6, 0, 1),
        (3, 3, 1),
        (7, 4, 2),
    ],
)
def test_abnormal_feature_count(
    turn,
    revisit,
    expected_count,
):
    result = predict_anomaly(
        turn_10min=turn,
        revisit_15min=revisit,
    )

    assert (
        result["abnormal_feature_count"]
        == expected_count
    )