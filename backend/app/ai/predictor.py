"""Isolation Forest를 ReplayService 계약에 맞춰 안전하게 감싼다."""

from __future__ import annotations

import json
import logging
from math import exp, isfinite
from pathlib import Path
from typing import Any

try:
    import joblib
    import pandas as pd
    import sklearn
except Exception:  # 선택 의존성이 깨져도 API 서버는 규칙 모드로 실행한다.
    joblib = None
    pd = None
    sklearn = None


logger = logging.getLogger(__name__)

AI_DIR = Path(__file__).resolve().parent
MODEL_PATH = AI_DIR / "artifacts" / "isolation_forest.joblib"
META_PATH = AI_DIR / "artifacts" / "model_meta.json"
MODEL_FEATURES = ("turn_10min", "revisit_15min")
LEGACY_FEATURES = {
    "turn_10min": "turn_count",
    "revisit_15min": "revisit_count",
}


def _fallback_prediction() -> dict[str, Any]:
    return {
        "anomaly_score": None,
        "is_anomaly": None,
        "is_unusual": None,
        "is_very_unusual": None,
        "model_mode": "rule_fallback",
    }


def _normalized_score(raw_score: float, p95: float, p99: float) -> float:
    """Raw score를 API의 0~1 UI 점수로 변환하며 P95/P99 의미를 보존한다."""

    if not all(isfinite(value) for value in (raw_score, p95, p99)):
        raise ValueError("model score thresholds must be finite")
    if p95 <= 0 or p99 <= p95:
        raise ValueError("model score thresholds are invalid")

    normal_floor = max(0.0, p95 - (p99 - p95))
    if raw_score <= normal_floor:
        normalized = 0.0
    elif raw_score <= p95:
        normalized = 0.65 * (raw_score - normal_floor) / (p95 - normal_floor)
    elif raw_score <= p99:
        normalized = 0.65 + 0.20 * (raw_score - p95) / (p99 - p95)
    else:
        # P99 이상은 0.85부터 완만하게 1.0에 수렴시켜 범위를 벗어나지 않게 한다.
        normalized = 0.85 + 0.15 * (
            1.0 - exp(-(raw_score - p99) / (p99 - p95))
        )
    return round(min(1.0, max(0.0, normalized)), 6)


def _feature_count(features: dict[str, Any], name: str) -> int:
    value = features.get(name)
    if value is None:
        value = features.get(LEGACY_FEATURES[name])
    if isinstance(value, bool):
        raise ValueError("model feature must be a non-negative integer")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("model feature must be a non-negative integer") from exc
    if not isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError("model feature must be a non-negative integer")
    return int(number)


def _metadata_threshold(metadata: dict[str, Any], name: str) -> float:
    value = metadata.get("anomaly_score_thresholds", {}).get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("model threshold must be numeric")
    threshold = float(value)
    if not isfinite(threshold):
        raise ValueError("model threshold must be finite")
    return threshold


class IsolationForestPredictor:
    """모델 사용 가능 여부와 관계없이 ReplayService 호출 규약을 지킨다."""

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        metadata_path: Path = META_PATH,
    ) -> None:
        self.model: Any = None
        self.metadata: dict[str, Any] = {}
        self.p95: float | None = None
        self.p99: float | None = None
        self.ready = False
        self._load(model_path, metadata_path)

    def _load(self, model_path: Path, metadata_path: Path) -> None:
        if joblib is None or pd is None or sklearn is None:
            logger.warning("AI dependencies unavailable; using rule fallback")
            return
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if tuple(metadata.get("features", ())) != MODEL_FEATURES:
                raise ValueError("model feature metadata mismatch")
            if metadata.get("model_type") != "IsolationForest":
                raise ValueError("model type metadata mismatch")
            if metadata.get("raw_score_source") != "negative_score_samples":
                raise ValueError("raw score metadata mismatch")
            if metadata.get("score_direction") != "higher_is_more_anomalous":
                raise ValueError("score direction metadata mismatch")

            expected_version = metadata.get("library_versions", {}).get(
                "scikit_learn"
            )
            if expected_version != sklearn.__version__:
                raise ValueError("scikit-learn version mismatch")

            p95 = _metadata_threshold(metadata, "p95")
            p99 = _metadata_threshold(metadata, "p99")
            _normalized_score(p95, p95, p99)

            model = joblib.load(model_path)
            if not callable(getattr(model, "score_samples", None)):
                raise TypeError("model does not provide score_samples")
            if model.__class__.__name__ != metadata["model_type"]:
                raise TypeError("model artifact type mismatch")
            model_features = tuple(getattr(model, "feature_names_in_", ()))
            if model_features and model_features != MODEL_FEATURES:
                raise ValueError("model artifact feature mismatch")
        except Exception:
            logger.warning("AI model unavailable or incompatible; using rule fallback")
            return

        self.model = model
        self.metadata = metadata
        self.p95 = p95
        self.p99 = p99
        self.ready = True

    def __call__(self, features: dict[str, Any]) -> dict[str, Any]:
        if not self.ready or self.model is None or self.p95 is None or self.p99 is None:
            return _fallback_prediction()
        try:
            values = {
                feature: _feature_count(features, feature)
                for feature in MODEL_FEATURES
            }
            frame = pd.DataFrame([values], columns=MODEL_FEATURES)
            raw_score = float(-self.model.score_samples(frame)[0])
            normalized = _normalized_score(raw_score, self.p95, self.p99)
        except Exception:
            logger.warning("AI inference failed; using rule fallback")
            return _fallback_prediction()

        return {
            "anomaly_score": normalized,
            "is_anomaly": raw_score >= self.p95,
            "is_unusual": raw_score >= self.p95,
            "is_very_unusual": raw_score >= self.p99,
            "model_mode": "isolation_forest",
        }


predictor = IsolationForestPredictor()


def predict_anomaly(features: dict[str, Any]) -> dict[str, Any]:
    """ReplayService에 주입하는 공개 adapter 함수."""

    return predictor(features)


def is_model_ready() -> bool:
    return predictor.ready
