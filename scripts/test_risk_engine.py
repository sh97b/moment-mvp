from backend.app.ai.predictor import predict_anomaly

from backend.app.ai.risk_engine import (
    determine_initial_risk,
)


def test_case(
    turn_10min: int,
    revisit_15min: int,
):
    # 1. Isolation Forest + Feature 이상 여부 계산
    prediction = predict_anomaly(
        turn_10min=turn_10min,
        revisit_15min=revisit_15min,
    )

    # 2. 초기 위험 단계 판단
    risk_level = determine_initial_risk(
        prediction
    )

    print("=" * 60)

    print(
        f"입력: "
        f"turn_10min={turn_10min}, "
        f"revisit_15min={revisit_15min}"
    )

    print(
        f"turn_abnormal: "
        f"{prediction['turn_abnormal']}"
    )

    print(
        f"revisit_abnormal: "
        f"{prediction['revisit_abnormal']}"
    )

    print(
        f"abnormal_feature_count: "
        f"{prediction['abnormal_feature_count']}"
    )

    print(
        f"anomaly_score: "
        f"{prediction['anomaly_score']:.4f}"
    )

    print(
        f"risk_level: {risk_level}"
    )


def main():

    test_cases = [
        # 둘 다 정상
        (3, 0),

        # 방향전환만 이상
        (6, 0),

        # 재방문만 이상
        (3, 3),

        # 둘 다 이상
        (7, 4),
    ]

    for turn, revisit in test_cases:
        test_case(
            turn_10min=turn,
            revisit_15min=revisit,
        )


if __name__ == "__main__":
    main()