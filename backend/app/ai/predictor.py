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


# =========================================
# Fallback 기본값
# =========================================

DEFAULT_FEATURE_COLUMNS = [
    "turn_10min",
    "revisit_15min",
]

FALLBACK_TURN_NORMAL_MAX = 4
FALLBACK_REVISIT_NORMAL_MAX = 1


# =========================================
# 모델 / Metadata 로드
# =========================================

model = None
metadata = {}

MODEL_MODE = "rule_fallback"

try:
    model = joblib.load(MODEL_PATH)

    with open(
        META_PATH,
        "r",
        encoding="utf-8",
    ) as f:
        metadata = json.load(f)

    MODEL_MODE = "isolation_forest"

except Exception as e:
    print(
        "[AI WARNING] Isolation Forest 로드 실패. "
        f"Rule fallback을 사용합니다: {e}"
    )


FEATURE_COLUMNS = metadata.get(
    "features",
    DEFAULT_FEATURE_COLUMNS,
)


normal_feature_max = metadata.get(
    "normal_feature_max",
    {},
)

TURN_NORMAL_MAX = normal_feature_max.get(
    "turn_10min",
    FALLBACK_TURN_NORMAL_MAX,
)

REVISIT_NORMAL_MAX = normal_feature_max.get(
    "revisit_15min",
    FALLBACK_REVISIT_NORMAL_MAX,
)


thresholds = metadata.get(
    "anomaly_score_thresholds",
    {},
)

P95 = thresholds.get("p95")
P99 = thresholds.get("p99")


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
    # Isolation Forest 사용 가능 시
    if model is not None:
        anomaly_score = float(
            -model.score_samples(
                current[FEATURE_COLUMNS]
            )[0]
        )

        is_unusual = (
            anomaly_score >= P95
            if P95 is not None
            else None
        )

        is_very_unusual = (
            anomaly_score >= P99
            if P99 is not None
            else None
        )

    # 모델 사용 불가능 시 Rule fallback
    else:
        anomaly_score = None
        is_unusual = None
        is_very_unusual = None


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
        "is_unusual": is_unusual,
        "is_very_unusual": is_very_unusual,

        "model_mode": MODEL_MODE,
    }