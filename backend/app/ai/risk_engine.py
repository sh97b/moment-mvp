# =========================================
# 위험 단계 상수
# =========================================

NORMAL = 0
INTEREST = 1
CAUTION = 2
DANGER = 3


def get_effective_abnormal_count(
    prediction: dict,
) -> int:
    """
    최종 위험 판단에 실제로 사용할
    이상 Feature 개수를 반환한다.

    Isolation Forest 사용 시:
    - is_unusual=True일 때만 Feature 이상을 인정한다.
    - is_unusual=False이면 정상으로 처리한다.

    Rule fallback 사용 시:
    - Isolation Forest 결과가 없으므로
      Feature Rule만 사용한다.
    """

    abnormal_count = prediction[
        "abnormal_feature_count"
    ]

    model_mode = prediction.get(
        "model_mode",
        "isolation_forest",
    )

    # -------------------------------------
    # Rule fallback
    # -------------------------------------

    if model_mode == "rule_fallback":
        return abnormal_count


    # -------------------------------------
    # Isolation Forest 사용
    # -------------------------------------

    is_unusual = prediction.get(
        "is_unusual"
    )

    # Isolation Forest가 평소와 다르다고
    # 판단한 경우에만 Feature 이상을 인정
    if is_unusual is True:
        return abnormal_count

    # Feature Rule에는 걸렸지만
    # Isolation Forest에서는 특이하지 않음
    return 0


def determine_initial_risk(
    prediction: dict,
) -> int:
    """
    현재 한 시점의 유효 이상 Feature 개수를
    기반으로 초기 위험 단계를 판단한다.

    0개 -> 정상
    1개 -> 관심
    2개 -> 주의

    3단계 위험은 Safety Loop에서 판단한다.
    """

    abnormal_count = (
        get_effective_abnormal_count(
            prediction
        )
    )

    if abnormal_count == 2:
        return CAUTION

    if abnormal_count == 1:
        return INTEREST

    return NORMAL