from backend.app.ai.predictor import predict_anomaly


def print_result(
    turn_10min: int,
    revisit_15min: int,
):
    result = predict_anomaly(
        turn_10min=turn_10min,
        revisit_15min=revisit_15min,
    )

    print("=" * 50)

    print(
        f"입력: "
        f"turn_10min={turn_10min}, "
        f"revisit_15min={revisit_15min}"
    )

    print(
        f"anomaly_score: "
        f"{result['anomaly_score']:.4f}"
    )

    print(
        f"turn_abnormal: "
        f"{result['turn_abnormal']}"
    )

    print(
        f"revisit_abnormal: "
        f"{result['revisit_abnormal']}"
    )

    print(
        f"abnormal_feature_count: "
        f"{result['abnormal_feature_count']}"
    )

    print(
        f"is_unusual: "
        f"{result['is_unusual']}"
    )

    print(
        f"is_very_unusual: "
        f"{result['is_very_unusual']}"
    )


def main():

    test_cases = [
        # 정상 예상
        (3, 0),

        # 방향전환만 이상 예상
        (6, 0),

        # 재방문만 이상 예상
        (3, 3),

        # 둘 다 이상 예상
        (7, 4),
    ]

    for turn, revisit in test_cases:
        print_result(
            turn_10min=turn,
            revisit_15min=revisit,
        )


if __name__ == "__main__":
    main()