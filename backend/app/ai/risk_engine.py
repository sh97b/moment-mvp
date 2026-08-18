# =========================================
# 위험 단계 상수
# =========================================

NORMAL = 0
INTEREST = 1
CAUTION = 2
DANGER = 3


def determine_initial_risk(
    prediction: dict,
) -> int:
    """
    현재 한 시점의 Feature 이상 개수로
    초기 위험 단계를 판단한다.

    이상 Feature 0개 -> 0단계 정상
    이상 Feature 1개 -> 1단계 관심
    이상 Feature 2개 -> 2단계 주의

    3단계 위험은 Safety Loop에서 별도로 판단한다.
    """

    abnormal_count = prediction[
        "abnormal_feature_count"
    ]

    # 방향전환 + 재방문 둘 다 이상
    if abnormal_count == 2:
        return CAUTION

    # 방향전환 또는 재방문 중 하나만 이상
    if abnormal_count == 1:
        return INTEREST

    # 둘 다 정상
    return NORMAL