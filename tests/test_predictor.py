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


def test_model_load_failure_uses_rule_fallback(
    monkeypatch,
):
    from backend.app.ai import predictor

    # joblib.load가 실패하는 상황을 강제로 만든다.
    def mock_load_failure(*args, **kwargs):
        raise OSError("model load failed")

    monkeypatch.setattr(
        predictor.joblib,
        "load",
        mock_load_failure,
    )

    # 모델 로딩 함수 실행
    model, metadata, model_mode = (
        predictor.load_model_and_metadata()
    )

    # fallback이 제대로 적용되는지 확인
    assert model is None
    assert metadata == {}
    assert model_mode == "rule_fallback"