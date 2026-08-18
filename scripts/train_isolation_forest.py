from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split


# =========================================
# 경로 설정
# =========================================

ROOT_DIR = Path(__file__).resolve().parents[1]

BASELINE_PATH = (
    ROOT_DIR
    / "data"
    / "processed"
    / "baseline_data.csv"
)


# =========================================
# Isolation Forest 입력 Feature
# =========================================

FEATURE_COLUMNS = [
    "turn_10min",
    "revisit_15min",
]


def main():

    # -----------------------------------------
    # 1. Baseline 데이터 읽기
    # -----------------------------------------

    df = pd.read_csv(BASELINE_PATH)

    print("=== Baseline Load ===")
    print(f"전체 행: {len(df)}")
    print(f"전체 경로: {df['route_id'].nunique()}")


    # -----------------------------------------
    # 2. route_id 목록 추출
    # -----------------------------------------

    route_ids = df["route_id"].unique()

    print(f"\n전체 route_id 개수: {len(route_ids)}")


    # -----------------------------------------
    # 3. 경로 단위 Train / Validation 분리
    # -----------------------------------------

    train_routes, val_routes = train_test_split(
        route_ids,
        test_size=0.2,
        random_state=42,
    )


    # -----------------------------------------
    # 4. 실제 데이터 분리
    # -----------------------------------------

    train_df = df[
        df["route_id"].isin(train_routes)
    ].copy()

    val_df = df[
        df["route_id"].isin(val_routes)
    ].copy()


    # -----------------------------------------
    # 5. 결과 확인
    # -----------------------------------------

    print("\n=== Train ===")
    print(f"경로 개수: {train_df['route_id'].nunique()}")
    print(f"행 개수: {len(train_df)}")

    print("\n=== Validation ===")
    print(f"경로 개수: {val_df['route_id'].nunique()}")
    print(f"행 개수: {len(val_df)}")


    # -----------------------------------------
    # 6. Isolation Forest에 들어갈 X
    # -----------------------------------------

    X_train = train_df[FEATURE_COLUMNS]
    X_val = val_df[FEATURE_COLUMNS]

    print("\n=== X_train ===")
    print(X_train.head())

    print("\n=== X_val ===")
    print(X_val.head())


if __name__ == "__main__":
    main()