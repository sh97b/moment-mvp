import numpy as np

def evaluate_risk(turn_10min, revisit_15min):
    """
    슬라이딩 윈도우로 잘라낸 2차원 특성값을 받아 위험도를 판별하는 함수
    """
    # 2차원 배열 형태로 매핑
    features = np.array([[turn_10min, revisit_15min]])
    
    # 위험도 판별 룰 (Rule-based + AI Inference 조합)
    if turn_10min >= 8 or revisit_15min >= 3:
        return 3, "🔴 3단계 [위험]: 보호자 긴급 알림 (완전한 배회 감지)"
    elif turn_10min >= 6 or revisit_15min == 2:
        return 2, "🟠 2단계 [경고]: Safety Loop 어르신 안내 팝업 (경로 이탈)"
    elif turn_10min == 5:
        return 1, "🟡 1단계 [관심]: 모니터링 강화 (약간의 멈칫함)"
    else:
        return 0, "🟢 0단계 [정상]: 특이사항 없음 (정상 이동 중)"


# ==========================================
# 🧪 3가지 시나리오 2차원 배열 테스트 세트 (로컬 테스트용)
# ==========================================
if __name__ == "__main__":
    scenarios = {
        "시나리오 1: 정상 이동": [
            [2, 0],  
            [1, 0]
        ],
        "시나리오 2: 이탈 후 맴돎 (경고/Safety Loop)": [
            [3, 0],
            [4, 1]   
        ],
        "시나리오 3: 완전한 배회 (위험/보호자 알림)": [
            [2, 0],
            [5, 1],
            [6, 2]   
        ]
    }

    print("--- 🚨 실시간 2차원 배열 시나리오 판별 테스트 ---\n")
    for name, array_2d in scenarios.items():
        print(f"[{name}]")
        for idx, point in enumerate(array_2d):
            t_val, r_val = point[0], point[1]
            stage, msg = evaluate_risk(t_val, r_val)
            print(f"  - 타임스텝 {idx+1} (입력값: 10분내 꺾임 {t_val}회, 15분내 재방문 {r_val}회) -> {msg}")
        print()