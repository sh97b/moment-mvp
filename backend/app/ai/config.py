# ============================================================
# MOMENT AI Feature Configuration
# ============================================================


# ------------------------------------------------------------
# 1. Isolation Forest 학습에 사용하는 개인 생활패턴 Feature
# ------------------------------------------------------------
#
# 이 Feature들은 "이 사용자가 평소 어떻게 외출하는가?"를 나타냅니다.
#
# 정상 이동 데이터의 이 5개 Feature를 Isolation Forest가 학습합니다.
#

MODEL_FEATURE_COLUMNS = [
    "outing_duration_min",                 # 외출 지속시간 (분)
    "total_distance_m",                    # 총 이동거리 (m)
    "max_home_distance_m",                 # 집에서 최대 이탈거리 (m)
    "return_time_deviation_min",           # 평소 귀가시간 대비 편차 (분)
    "outside_living_area_duration_min",    # 생활권 밖 체류시간 (분)
]


# ------------------------------------------------------------
# 2. Rule 기반 이상행동 판단에 사용하는 이동 형태 Feature
# ------------------------------------------------------------
#
# 이 Feature들은 Isolation Forest의 학습 입력으로 사용하지 않습니다.
#
# "현재 이동이 배회 형태를 보이는가?"를
# 명시적인 Rule로 판단하기 위해 사용합니다.
#

RULE_FEATURE_COLUMNS = [
    "turn_count",                          # 방향전환 횟수
    "revisit_count",                       # 동일 지역 재방문 횟수
    "repeated_segment",                    # 동일 구간 반복 여부 (0 / 1)
    "local_movement_duration_min",         # 일정 반경 내 이동 지속시간 (분)
    "home_distance_trend_m_per_min",       # 집과의 거리 변화 추세 (m/min)
]


# ------------------------------------------------------------
# 3. 데이터 식별 및 평가용 컬럼
# ------------------------------------------------------------
#
# 모델 입력에는 들어가지 않습니다.
#

META_COLUMNS = [
    "scenario_id",
    "frame_id",
    "label",
]


# ------------------------------------------------------------
# 4. Isolation Forest 기본 설정
# ------------------------------------------------------------

RANDOM_STATE = 42

N_ESTIMATORS = 300

DEFAULT_THRESHOLD_QUANTILE = 0.95