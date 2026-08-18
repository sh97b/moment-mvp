from pathlib import Path
import json

import joblib
import pandas as pd


# =========================================
# 경로 설정
# =========================================

AI_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = AI_DIR / "artifacts"

MODEL_PATH = ARTIFACT_DIR / "isolation_forest.joblib"
META_PATH = ARTIFACT_DIR / "model_meta.json"


# =========================================
# 모델 / Metadata 로드
# =========================================

model = joblib.load(MODEL_PATH)

with open(
    META_PATH,
    "r",
    encoding="utf-8",
) as f:
    metadata = json.load(f)


FEATURE_COLUMNS = metadata["features"]

TURN_NORMAL_MAX = metadata[
    "normal_feature_max"
]["turn_10min"]

REVISIT_NORMAL_MAX = metadata[
    "normal_feature_max"
]["revisit_15min"]

P95 = metadata[
    "anomaly_score_thresholds"
]["p95"]

P99 = metadata[
    "anomaly_score_thresholds"
]["p99"]


# =========================================
# 추론 함수
# =========================================

def predict_anomaly(
    turn_10min: int,
    revisit_15min: int,
) -> dict:

    # 1. 입력 검증
    if turn_10min < 0:
        raise ValueError(
            "turn_10min은 0 이상이어야 합니다."
        )

    if revisit_15min < 0:
        raise ValueError(
            "revisit_15min은 0 이상이어야 합니다."
        )


    # 2. 모델 입력 형태 생성
    current = pd.DataFrame(
        [
            {
                "turn_10min": turn_10min,
                "revisit_15min": revisit_15min,
            }
        ]
    )


    # 3. Isolation Forest 이상점수
    #
    # score_samples는 낮을수록 이상하므로
    # -를 붙여 우리 프로젝트에서는
    # 높을수록 이상하도록 사용
    anomaly_score = float(
        -model.score_samples(
            current[FEATURE_COLUMNS]
        )[0]
    )


    # 4. 각 Feature가 정상 Baseline을
    #    벗어났는지 판단
    turn_abnormal = (
        turn_10min > TURN_NORMAL_MAX
    )

    revisit_abnormal = (
        revisit_15min > REVISIT_NORMAL_MAX
    )


    # 5. 이상 Feature 개수
    abnormal_feature_count = (
        int(turn_abnormal)
        + int(revisit_abnormal)
    )


    # 6. 결과 반환
    return {
        "turn_10min": turn_10min,
        "revisit_15min": revisit_15min,

        "anomaly_score": anomaly_score,

        "turn_abnormal": turn_abnormal,
        "revisit_abnormal": revisit_abnormal,

        "abnormal_feature_count":
            abnormal_feature_count,

        # Isolation Forest 기준은
        # 참고 정보로 유지
        "is_unusual": anomaly_score >= P95,
        "is_very_unusual": anomaly_score >= P99,
    }