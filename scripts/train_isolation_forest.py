from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

import sklearn

from sklearn.ensemble import IsolationForest
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

ARTIFACT_DIR = (
    ROOT_DIR
    / "backend"
    / "app"
    / "ai"
    / "artifacts"
)

MODEL_PATH = (
    ARTIFACT_DIR
    / "isolation_forest.joblib"
)

META_PATH = (
    ARTIFACT_DIR
    / "model_meta.json"
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

    # -----------------------------------------
    # 7. Isolation Forest 모델 생성
    # -----------------------------------------

    model = IsolationForest(
        n_estimators=200,
        max_samples="auto",
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )


    # -----------------------------------------
    # 8. 정상 Baseline 학습
    # -----------------------------------------

    model.fit(X_train)

    print("\n=== Isolation Forest 학습 완료 ===")


    # -----------------------------------------
    # 9. Train anomaly score 계산
    # -----------------------------------------

    train_scores = -model.score_samples(X_train)


    # -----------------------------------------
    # 10. Validation anomaly score 계산
    # -----------------------------------------

    val_scores = -model.score_samples(X_val)


    # -----------------------------------------
    # 11. Score 통계 확인
    # -----------------------------------------

    print("\n=== Train anomaly score ===")
    print(f"평균: {train_scores.mean():.4f}")
    print(f"최소: {train_scores.min():.4f}")
    print(f"최대: {train_scores.max():.4f}")


    print("\n=== Validation anomaly score ===")
    print(f"평균: {val_scores.mean():.4f}")
    print(f"최소: {val_scores.min():.4f}")
    print(f"최대: {val_scores.max():.4f}")


    # -----------------------------------------
    # 12. 정상 Validation 기준점 계산
    # -----------------------------------------

    p90 = np.percentile(val_scores, 90)
    p95 = np.percentile(val_scores, 95)
    p99 = np.percentile(val_scores, 99)


    print("\n=== Validation score percentile ===")

    print(f"P90: {p90:.4f}")
    print(f"P95: {p95:.4f}")
    print(f"P99: {p99:.4f}")

    # -----------------------------------------
    # 13. Feature 조합별 anomaly score 확인
    # -----------------------------------------

    score_df = X_val.copy()

    score_df["anomaly_score"] = val_scores


    combo_scores = (
        score_df
        .groupby(FEATURE_COLUMNS)
        .agg(
            count=("anomaly_score", "size"),
            mean_score=("anomaly_score", "mean"),
            min_score=("anomaly_score", "min"),
            max_score=("anomaly_score", "max"),
        )
        .reset_index()
        .sort_values(
            "mean_score",
            ascending=True,
        )
    )


    print("\n=== Feature 조합별 anomaly score ===")

    print(
        combo_scores.to_string(
            index=False
        )
    )

    # -----------------------------------------
    # 14. 정상 Baseline Feature 범위 계산
    # -----------------------------------------

    turn_normal_max = int(
        X_train["turn_10min"].max()
    )

    revisit_normal_max = int(
        X_train["revisit_15min"].max()
    )


    print("\n=== 정상 Baseline Feature 기준 ===")

    print(
        f"turn_10min 정상 최대값: "
        f"{turn_normal_max}"
    )

    print(
        f"revisit_15min 정상 최대값: "
        f"{revisit_normal_max}"
    )


    # -----------------------------------------
    # 15. artifacts 폴더 생성
    # -----------------------------------------

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------
    # 16. Isolation Forest 모델 저장
    # -----------------------------------------

    joblib.dump(
        model,
        MODEL_PATH,
    )


    # -----------------------------------------
    # 17. 모델 Metadata 저장
    # -----------------------------------------

    metadata = {
    "features": FEATURE_COLUMNS,

    "normal_feature_max": {
        "turn_10min": turn_normal_max,
        "revisit_15min": revisit_normal_max,
    },

    "anomaly_score_thresholds": {
        "p90": float(p90),
        "p95": float(p95),
        "p99": float(p99),
    },

    "model_config": {
        "n_estimators": 200,
        "max_samples": "auto",
        "contamination": "auto",
        "random_state": 42,
    },

    "library_versions": {
        "scikit_learn": sklearn.__version__,
    },

    "training_info": {
        "train_routes": int(
            train_df["route_id"].nunique()
        ),
        "validation_routes": int(
            val_df["route_id"].nunique()
        ),
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
    },
}


    with open(
        META_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2,
        )


    # -----------------------------------------
    # 18. 저장 결과 출력
    # -----------------------------------------

    print("\n=== Artifact 저장 완료 ===")

    print(f"Model: {MODEL_PATH}")
    print(f"Metadata: {META_PATH}")




if __name__ == "__main__":
    main()