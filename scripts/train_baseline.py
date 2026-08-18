import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def create_and_train_baseline():
    np.random.seed(42)
    n_samples = 500  # 평소 30일간의 정상 외출 기록 (500회 누적)

    # -------------------------------------------------------------
    # 1. 개인 생활패턴 기준 분포 (Baseline Profile)
    # -------------------------------------------------------------
    outing_duration_hr = np.random.normal(loc=1.5, scale=0.3, size=n_samples).clip(0.5, 3.5)
    total_distance_m = outing_duration_hr * np.random.normal(loc=1200, scale=150, size=n_samples)
    max_deviation_m = np.random.exponential(scale=20.0, size=n_samples).clip(5.0, 80.0)
    return_time_diff_min = np.random.normal(loc=0.0, scale=10.0, size=n_samples).clip(-30.0, 30.0)
    stay_outside_living_min = np.zeros(n_samples)  # 평소에는 생활권 이탈 0분

    df_baseline = pd.DataFrame({
        "outing_duration_hr": np.round(outing_duration_hr, 2),
        "total_distance_m": np.round(total_distance_m, 1),
        "max_deviation_from_home_m": np.round(max_deviation_m, 1),
        "return_time_diff_min": np.round(return_time_diff_min, 1),
        "stay_outside_living_area_min": stay_outside_living_min
    })

    # 생활패턴 기준선 기반 이상치 모델 피팅
    model = IsolationForest(n_estimators=100, contamination=0.03, random_state=42)
    model.fit(df_baseline)

    os.makedirs("backend/artifacts", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    joblib.dump(model, "backend/artifacts/isolation_forest.joblib")
    df_baseline.to_csv("data/processed/normal_baseline.csv", index=False)

    print("✅ [1단계] 개인 생활패턴 기준 데이터셋 생성: data/processed/normal_baseline.csv")
    print("✅ [2단계] 생활패턴 베이스라인 모델 학습 완료: backend/artifacts/isolation_forest.joblib")

if __name__ == "__main__":
    create_and_train_baseline()