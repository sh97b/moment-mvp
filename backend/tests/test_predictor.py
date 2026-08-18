import json
from pathlib import Path

import pytest

from backend.app.ai.predictor import (
    META_PATH,
    MODEL_PATH,
    IsolationForestPredictor,
    _normalized_score,
    is_model_ready,
    predict_anomaly,
    predictor,
)
from backend.app import main
from backend.app.main import health, replay_service


def test_model_artifact_loads_with_pinned_dependencies() -> None:
    assert is_model_ready() is True


def test_application_uses_model_predictor_for_replay() -> None:
    expected = predict_anomaly({"turn_count": 0, "revisit_count": 0})
    replay = replay_service.build_replay("normal")

    assert replay_service.predictor is predict_anomaly
    assert health()["model_ready"] is True
    assert replay.frames[0].anomaly_score == expected["anomaly_score"]


def test_health_stays_ok_when_model_is_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(main, "is_model_ready", lambda: False)

    result = health()

    assert result["status"] == "ok"
    assert result["model_ready"] is False


def test_predictor_accepts_api_and_window_feature_names_deterministically() -> None:
    api_features = {"turn_count": 9, "revisit_count": 3}
    window_features = {"turn_10min": 9, "revisit_15min": 3}

    first = predict_anomaly(api_features)
    second = predict_anomaly(api_features)

    assert first == second == predict_anomaly(window_features)
    assert first["model_mode"] == "isolation_forest"
    assert first["is_anomaly"] is True
    assert first["is_very_unusual"] is True
    assert 0 <= first["anomaly_score"] <= 1
    assert first["anomaly_score"] > predict_anomaly(
        {"turn_count": 0, "revisit_count": 0}
    )["anomaly_score"]


def test_raw_score_normalization_preserves_model_thresholds() -> None:
    assert _normalized_score(0.4, 0.6, 0.8) < 0.65
    assert _normalized_score(0.6, 0.6, 0.8) == 0.65
    assert _normalized_score(0.8, 0.6, 0.8) == 0.85
    assert 0.85 < _normalized_score(1.0, 0.6, 0.8) <= 1


def test_metadata_records_model_and_score_semantics() -> None:
    metadata = json.loads(META_PATH.read_text(encoding="utf-8"))

    assert metadata["model_type"] == "IsolationForest"
    assert metadata["raw_score_source"] == "negative_score_samples"
    assert metadata["score_direction"] == "higher_is_more_anomalous"
    assert metadata["features"] == ["turn_10min", "revisit_15min"]
    assert set(metadata["anomaly_score_thresholds"]) >= {"p95", "p99"}


@pytest.mark.parametrize(
    "thresholds",
    [
        {"p95": 0.6, "p99": 0.6},
        {"p95": 0.8, "p99": 0.6},
        {"p95": 0.6},
        {"p95": "0.6", "p99": 0.8},
        {"p95": 0.6, "p99": "0.8"},
        {"p95": float("nan"), "p99": 0.8},
        {"p95": 0.6, "p99": float("inf")},
    ],
)
def test_invalid_metadata_thresholds_use_rule_fallback(
    tmp_path: Path, thresholds: dict[str, object]
) -> None:
    metadata = json.loads(META_PATH.read_text(encoding="utf-8"))
    metadata["anomaly_score_thresholds"] = thresholds
    metadata_path = tmp_path / "model_meta.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    unavailable = IsolationForestPredictor(
        model_path=MODEL_PATH,
        metadata_path=metadata_path,
    )

    assert unavailable.ready is False
    assert unavailable({"turn_count": 9, "revisit_count": 3})["model_mode"] == "rule_fallback"


def test_missing_model_uses_rule_fallback(tmp_path: Path) -> None:
    unavailable = IsolationForestPredictor(
        model_path=tmp_path / "missing.joblib",
        metadata_path=META_PATH,
    )

    assert unavailable.ready is False
    assert unavailable({"turn_count": 9, "revisit_count": 3}) == {
        "anomaly_score": None,
        "is_anomaly": None,
        "is_unusual": None,
        "is_very_unusual": None,
        "model_mode": "rule_fallback",
    }


def test_inference_error_and_invalid_features_use_rule_fallback(monkeypatch) -> None:
    class BrokenModel:
        def score_samples(self, _frame):
            raise RuntimeError("inference failed")

    monkeypatch.setattr(predictor, "model", BrokenModel())
    failed = predict_anomaly({"turn_count": 9, "revisit_count": 3})
    assert failed["model_mode"] == "rule_fallback"
    assert failed["anomaly_score"] is None
    assert failed["is_anomaly"] is None

    invalid = predict_anomaly({"turn_count": float("nan"), "revisit_count": 0})
    assert invalid["model_mode"] == "rule_fallback"
