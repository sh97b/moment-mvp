from backend.app.ai.predictor import predict_anomaly
from backend.app.ai.safety_loop import SafetyLoop


def main():

    safety_loop = SafetyLoop()

    # 시간 흐름을 가정한 테스트 데이터
    #
    # 현재 Baseline:
    # turn 정상 최대 = 4
    # revisit 정상 최대 = 1

    test_sequence = [
        # timestamp, turn, revisit

        # 정상
        ("09:10", 3, 0),

        # 방향전환 하나만 이상 → 관심
        ("09:11", 6, 0),

        # 관심 상태에서 이상 지속
        ("09:12", 6, 0),
        ("09:13", 7, 0),
        ("09:14", 7, 0),

        # 여기서 3분 지속 → 주의 예상

        # 주의 상태에서도 계속 이상
        ("09:15", 8, 1),
        ("09:16", 8, 2),
        ("09:17", 9, 3),

        # 여기서 3분 지속 → 위험 예상

        # 위험 상태 유지
        ("09:18", 9, 4),

        # 정상화 시작
        ("09:19", 3, 0),

        # 계속 정상
        ("09:20", 3, 0),
        ("09:21", 3, 0),
    ]

    print(
        f"{'time':<8}"
        f"{'turn':<7}"
        f"{'revisit':<9}"
        f"{'prev':<7}"
        f"{'level':<7}"
        f"{'streak':<8}"
        f"{'increase':<10}"
    )

    print("-" * 56)

    for timestamp, turn, revisit in test_sequence:

        # Isolation Forest + Feature 이상 판단
        prediction = predict_anomaly(
            turn_10min=turn,
            revisit_15min=revisit,
        )

        # Safety Loop
        result = safety_loop.update(
            prediction
        )

        print(
            f"{timestamp:<8}"
            f"{turn:<7}"
            f"{revisit:<9}"
            f"{result['previous_level']:<7}"
            f"{result['current_level']:<7}"
            f"{result['abnormal_streak']:<8}"
            f"{str(result['is_increasing']):<10}"
        )


if __name__ == "__main__":
    main()