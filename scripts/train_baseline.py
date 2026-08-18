import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def create_and_train_baseline():
    np.random.seed(42)
    n_samples = 500  # 평소 30일간의 정상 외출 데이터

    # 1. 정상 이동 특징값 분포 (Speed, Deviation, Angular Variance, Stay Time)
    speeds = np.random.normal(loc=3.2, scale=0.4, size=n_samples)
    deviations = np.random.exponential(scale=12.0, size=n_samples)
    angular_vars = np.random.beta(a=1, b=5, size=n_samples) * 0.2
    stay_durations = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.7, 0.2, 0.08, 0.02])

    df_train = pd.DataFrame({
        "speed_kmh": np.clip(speeds, 1.5, 5.0),
        "deviation_distance_m": deviations,
        "angular_variance": angular_vars,
        "stay_duration_min": stay_durations
    })

    # 2. Isolation Forest 학습
    model = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=42
    )
    model.fit(df_train)

    # 3. 모델 아티팩트 및 처리 데이터 저장
    os.makedirs("backend/artifacts", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    joblib.dump(model, "backend/artifacts/isolation_forest.joblib")
    df_train.to_csv("data/processed/normal_baseline.csv", index=False)

    print("✅ Baseline 모델 학습 완료: backend/artifacts/isolation_forest.joblib")
    print("✅ 정상 기준 CSV 생성 완료: data/processed/normal_baseline.csv")

if __name__ == "__main__":
    create_and_train_baseline()