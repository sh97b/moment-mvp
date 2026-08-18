"""데이터 로딩, 선택적 AI 추론, Safety Loop와 API frame 조립을 연결한다."""

import logging
from math import isfinite
from typing import Any, Callable

from backend.app.models.replay import Alert, FrameFeatures, ReplayFrame, ReplayResponse
from backend.app.services.safety_loop import SafetyState, evaluate_safety
from backend.app.services.scenario_loader import ScenarioLoader

logger = logging.getLogger(__name__)
Predictor = Callable[[dict[str, Any]], dict[str, Any]]


class ReplayService:
    """한 replay 요청의 모든 frame을 독립된 Safety Loop 상태로 계산한다."""

    def __init__(self, loader: ScenarioLoader, predictor: Predictor | None = None):
        self.loader = loader
        self.predictor = predictor

    @staticmethod
    def _validated_prediction(score_value: Any, flag_value: Any) -> tuple[float | None, bool | None]:
        if isinstance(score_value, bool):
            return None, None
        try:
            score = float(score_value)
        except (TypeError, ValueError):
            return None, None
        if not isfinite(score) or not 0 <= score <= 1 or not isinstance(flag_value, bool):
            return None, None
        return score, flag_value

    def _prediction(self, features: dict[str, Any], raw_score: Any, raw_flag: Any) -> tuple[Any, Any]:
        # predictor가 연결됐더라도 예외·누락·비정상 출력이면 규칙 계산으로 복귀한다.
        if self.predictor is not None:
            try:
                prediction = self.predictor(features)
                return self._validated_prediction(
                    prediction.get("anomaly_score"), prediction.get("is_anomaly")
                )
            except Exception:
                logger.warning("AI inference failed; using rule fallback", exc_info=True)
                return None, None
        return self._validated_prediction(raw_score, raw_flag)

    def build_replay(self, scenario_id: str) -> ReplayResponse:
        raw_frames = self.loader.load(scenario_id)
        # 요청마다 상태를 새로 생성해 사용자·반복 요청 사이의 상태 누출을 막는다.
        state = SafetyState()
        frames: list[ReplayFrame] = []
        for raw in raw_frames:
            features = raw.features.model_dump()
            score, flag = self._prediction(features, raw.anomaly_score, raw.is_anomaly)
            decision = evaluate_safety(
                features, state, model_score=score, model_is_anomaly=flag
            )
            state = decision.state
            elderly_alert = None
            guardian_alert = None
            if state.risk_level >= 1:
                elderly_alert = Alert(
                    title="잠시 경로를 확인해 주세요",
                    message="평소 이동 경로와 조금 달라요. 익숙한 길로 돌아가 볼까요?",
                )
            if state.risk_level == 2:
                guardian_alert = Alert(
                    title="이동 징후를 확인해 주세요",
                    message="평소와 다른 이동 징후가 이어지고 있습니다.",
                )
            elif state.risk_level == 3:
                guardian_alert = Alert(
                    title="보호자 확인이 필요합니다",
                    message="평소와 다른 이동 징후가 계속되어 직접 확인을 권합니다.",
                )
            frames.append(
                ReplayFrame(
                    timestamp=raw.timestamp,
                    lat=raw.lat,
                    lng=raw.lng,
                    # 내부 feature 중 API 계약에 정의된 네 필드만 공개한다.
                    features=FrameFeatures(
                        turn_count=raw.features.turn_count,
                        revisit_count=raw.features.revisit_count,
                        home_distance_m=raw.features.home_distance_m,
                        home_distance_delta_m=raw.features.home_distance_delta_m,
                    ),
                    anomaly_score=decision.anomaly_score,
                    risk_level=state.risk_level,
                    reasons=decision.reasons,
                    elderly_alert=elderly_alert,
                    guardian_alert=guardian_alert,
                )
            )
        return ReplayResponse(scenario_id=scenario_id, frames=frames)
