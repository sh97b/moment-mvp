from pathlib import Path

import pandas as pd


# 프로젝트 최상위 경로
ROOT_DIR = Path(__file__).resolve().parents[1]


# Baseline CSV 경로
BASELINE_PATH = (
    ROOT_DIR
    / "data"
    / "processed"
    / "baseline_data.csv"
)


FEATURE_COLUMNS = [
    "turn_10min",
    "revisit_15min",
]


def main():
    # 1. CSV 읽기
    df = pd.read_csv(BASELINE_PATH)

    print("=== Baseline 데이터 확인 ===")
    print(f"전체 행 개수: {len(df)}")
    print(f"경로 개수: {df['route_id'].nunique()}")

    print("\n=== 컬럼 ===")
    print(df.columns.tolist())

    print("\n=== 앞 5개 데이터 ===")
    print(df.head())

    print("\n=== 결측치 ===")
    print(df.isnull().sum())

    print("\n=== Feature 통계 ===")
    print(df[FEATURE_COLUMNS].describe())

    print("\n=== Feature 최소 / 최대 ===")

    print(
        "turn_10min:",
        df["turn_10min"].min(),
        "~",
        df["turn_10min"].max(),
    )

    print(
        "revisit_15min:",
        df["revisit_15min"].min(),
        "~",
        df["revisit_15min"].max(),
    )


if __name__ == "__main__":
    main()