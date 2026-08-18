from pathlib import Path
import sys

import pandas as pd

from backend.app.ai.predictor import predict_anomaly
from backend.app.ai.safety_loop import SafetyLoop


ROOT_DIR = Path(__file__).resolve().parents[1]

SCENARIO_PATH = (
    ROOT_DIR
    / "data"
    / "synthetic"
    / "scenario_data.csv"
)


def replay_route(route_id: str):

    # 전체 시나리오 CSV
    df = pd.read_csv(SCENARIO_PATH)

    # 선택한 route만 추출
    route_df = df[
        df["route_id"] == route_id
    ].copy()

    if route_df.empty:
        raise ValueError(
            f"존재하지 않는 route_id입니다: {route_id}"
        )

    # 시간 순서 정렬
    route_df = route_df.sort_values(
        "timestamp"
    )

    safety_loop = SafetyLoop()

    print(
        f"\n=== Scenario Replay: {route_id} ===\n"
    )

    print(
        f"{'time':<8}"
        f"{'turn':<7}"
        f"{'revisit':<9}"
        f"{'score':<9}"
        f"{'abnormal':<10}"
        f"{'prev':<7}"
        f"{'level':<7}"
        f"{'streak':<8}"
    )

    print("-" * 65)

    for _, row in route_df.iterrows():

        timestamp = row["timestamp"]

        turn = int(
            row["turn_10min"]
        )

        revisit = int(
            row["revisit_15min"]
        )

        prediction = predict_anomaly(
            turn_10min=turn,
            revisit_15min=revisit,
        )

        result = safety_loop.update(
            prediction
        )

        score = prediction[
            "anomaly_score"
        ]

        score_text = (
            f"{score:.4f}"
            if score is not None
            else "fallback"
        )

        print(
            f"{timestamp:<8}"
            f"{turn:<7}"
            f"{revisit:<9}"
            f"{score_text:<9}"
            f"{prediction['abnormal_feature_count']:<10}"
            f"{result['previous_level']:<7}"
            f"{result['current_level']:<7}"
            f"{result['abnormal_streak']:<8}"
        )


def main():

    if len(sys.argv) != 2:
        print(
            "사용법: "
            "python -m scripts.replay_scenario "
            "<route_id>"
        )
        return

    route_id = sys.argv[1]

    replay_route(route_id)


if __name__ == "__main__":
    main()