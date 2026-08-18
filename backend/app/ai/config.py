# ============================================================
# MOMENT AI Configuration
# ============================================================


# ------------------------------------------------------------
# 1. Isolation Forest 학습 Feature
# ------------------------------------------------------------
#
# normal_baseline.csv의 모든 데이터는
# 30일간의 "정상 외출" 데이터라고 가정합니다.
#
# Isolation Forest는 아래 5개 Feature의
# 정상적인 조합/분포를 학습합니다.
#

MODEL_FEATURE_COLUMNS = [
    "outing_duration_hr",
    "total_distance_m",
    "max_deviation_from_home_m",
    "return_time_diff_min",
    "stay_outside_living_area_min",
]


# ------------------------------------------------------------
# 2. 실시간 이동 형태 Rule Feature
# ------------------------------------------------------------
#
# 이 Feature들은 Isolation Forest 학습에 사용하지 않습니다.
# Scenario Replay 시 현재 배회 행동을 판단하는 데 사용합니다.
#

RULE_FEATURE_COLUMNS = [
    "turn_count",                  # 90도 이상 급격한 방향전환 횟수
    "revisit_count",               # 동일 격자/지점 재방문 횟수
    "repeat_section",              # 동일 골목/구간 반복 횟수 (0 이상 정수)
    "radius_stay_duration_min",    # 반경 100m 내 누적 체류시간
    "home_distance_trend",         # 집과의 거리 변화: 증가 / 유지 / 감소
]
# revisit_count
# → 같은 지점/격자를 다시 방문한 횟수

# repeat_section
# → 같은 골목/구간 자체를 다시 왕복한 횟수



# ------------------------------------------------------------
# 3. Isolation Forest 설정
# ------------------------------------------------------------

RANDOM_STATE = 42

N_ESTIMATORS = 300


# ------------------------------------------------------------
# 4. 초기 anomaly threshold 설정
# ------------------------------------------------------------
#
# Isolation Forest의 raw score와 서비스의 0~1 anomaly_score는
# 서로 다른 값입니다.
#
# 실제 0~1 score 변환 방법은 모델 구현 단계에서 따로 만듭니다.
#

DEFAULT_THRESHOLD_QUANTILE = 0.95


# ------------------------------------------------------------
# 5. 서비스 Risk Level 기준
# ------------------------------------------------------------
#
# 최종적으로 0~1 범위로 변환된 anomaly_score에 적용합니다.
#
# 0.00 ~ 0.40 : Level 0 정상
# 0.41 ~ 0.65 : Level 1 주의
# 0.66 ~ 0.85 : Level 2 경고
# 0.86 ~ 1.00 : Level 3 위험
#

RISK_LEVEL_1_THRESHOLD = 0.40
RISK_LEVEL_2_THRESHOLD = 0.65
RISK_LEVEL_3_THRESHOLD = 0.85