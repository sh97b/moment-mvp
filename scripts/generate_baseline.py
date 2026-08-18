import os
import random
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. 디렉토리 설정 (프로젝트 루트 기준 data/synthetic 폴더 자동 탐색)
# ---------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'synthetic')

os.makedirs(DATA_DIR, exist_ok=True)
output_path = os.path.join(DATA_DIR, 'baseline_sliding_window.csv')

# ---------------------------------------------------------
# 2. 데이터 생성 로직 (1분 단위 + 10분/15분 슬라이딩 윈도우)
# ---------------------------------------------------------
random.seed(42)
data = []

print("🚀 종로구 어르신 정상 경로 데이터 100개 생성을 시작합니다...")

for i in range(1, 101):
    route_id = f"ROUTE_{str(i).zfill(3)}"
    
    # 20 ~ 30분 사이 무작위 소요 시간 결정 (1분 단위)
    total_time = random.randint(20, 30)
    
    # 총 누적 turn_count는 3, 4, 5 중 하나
    total_turns = random.choice([3, 4, 5])
    
    # 총 누적 turn_count에 따른 revisit_count 확률 할당
    if total_turns == 3:
        total_revisits = 0
    elif total_turns == 5:
        total_revisits = 1
    else: # 4일 경우 50% 확률로 0 또는 1
        total_revisits = random.choice([0, 1])
        
    possible_minutes = list(range(1, total_time + 1))
    turn_minutes = sorted(random.sample(possible_minutes, total_turns))
    
    if total_revisits == 1:
        revisit_minutes = [random.choice(possible_minutes)]
    else:
        revisit_minutes = []
        
    start_time = datetime.strptime("09:00", "%H:%M")
    
    # 1분 간격으로 이동하면서 '최근 10분/15분' 슬라이딩 윈도우 데이터 기록
    for current_min in range(total_time + 1):
        current_time_str = (start_time + timedelta(minutes=current_min)).strftime("%H:%M")
        
        # 최근 10분 이내에 발생한 방향 전환 횟수
        turn_10min = sum(1 for m in turn_minutes if current_min - 10 < m <= current_min)
        
        # 최근 15분 이내에 발생한 재방문 횟수
        revisit_15min = sum(1 for m in revisit_minutes if current_min - 15 < m <= current_min)
            
        data.append([route_id, current_time_str, turn_10min, revisit_15min])

# ---------------------------------------------------------
# 3. CSV 파일 저장
# ---------------------------------------------------------
df = pd.DataFrame(data, columns=['route_id', 'timestamp', 'turn_10min', 'revisit_15min'])
df.to_csv(output_path, index=False)

print(f"✅ [완료] 데이터 파일이 저장되었습니다 -> {output_path}")