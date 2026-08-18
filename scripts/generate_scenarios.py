import json
import os
from datetime import datetime, timedelta

def generate_dataset():
    base_time = datetime(2026, 8, 18, 14, 0, 0)
    
    # -------------------------------------------------------------
    # Scenario A: 정상 이동 (종로3가 집 -> 서울노인복지센터 -> 집)
    # -------------------------------------------------------------
    coords_a = [
        (37.57182, 126.98921), (37.57245, 126.98860), (37.57350, 126.98750),
        (37.57460, 126.98630), (37.57520, 126.98580),
        (37.57460, 126.98630), (37.57350, 126.98750), (37.57182, 126.98921)
    ]
    frames_a = []
    for i, (lat, lng) in enumerate(coords_a):
        t = base_time + timedelta(minutes=i * 4)
        frames_a.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "features": {
                "speed_kmh": 3.1,
                "deviation_distance_m": 8.0,
                "angular_variance": 0.08,
                "stay_duration_min": 0
            },
            "anomaly_score": 0.04,
            "risk_level": 0,
            "reasons": [],
            "elderly_alert": "안전한 경로로 이동 중입니다.",
            "guardian_alert": "정상 이동 중 (목적지: 서울노인복지센터)"
        })

    # -------------------------------------------------------------
    # Scenario B: 일시 이탈 후 복귀
    # -------------------------------------------------------------
    raw_b = [
        (37.57520, 126.98580, 0, 0.04, 5.0, 0.05, [], None, None),
        (37.57460, 126.98630, 0, 0.08, 12.0, 0.10, [], None, None),
        (37.57380, 126.98820, 1, 0.58, 165.0, 0.42, ["평소 이동 경로에서 160m 이탈"], "평소 다니시던 길이 아닙니다. 큰길 방향을 확인하세요.", "일시적 경로 이탈 감지 (낙원상가 인근, 주의 관찰)"),
        (37.57310, 126.98890, 1, 0.62, 190.0, 0.48, ["경로 이탈 지속"], "종로3가역 큰길 방향으로 이동해 주세요.", "일시적 경로 이탈 지속"),
        (37.57245, 126.98860, 0, 0.12, 20.0, 0.15, ["정상 경로로 복귀함"], "정상 경로로 복귀하셨습니다.", "정상 경로 복귀 확인 (주의 해제)"),
        (37.57182, 126.98921, 0, 0.03, 6.0, 0.05, [], "집에 도착하셨습니다.", "안전 귀가 완료")
    ]
    frames_b = []
    for i, (lat, lng, risk, score, dev, ang, reasons, e_alert, g_alert) in enumerate(raw_b):
        t = base_time + timedelta(minutes=i * 4)
        frames_b.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "features": {
                "speed_kmh": 2.7 if risk == 0 else 1.8,
                "deviation_distance_m": dev,
                "angular_variance": ang,
                "stay_duration_min": 0 if risk == 0 else 8
            },
            "anomaly_score": score,
            "risk_level": risk,
            "reasons": reasons,
            "elderly_alert": e_alert,
            "guardian_alert": g_alert
        })

    # -------------------------------------------------------------
    # Scenario C: 지속 배회
    # -------------------------------------------------------------
    raw_c = [
        (37.57520, 126.98580, 0, 0.04, 5.0, 0.05, 0, [], None, None),
        (37.57390, 126.98910, 1, 0.52, 140.0, 0.35, 5, ["귀가 경로 이탈 시작"], "가시는 곳을 다시 확인해 보세요.", "경로 이탈 감지"),
        (37.57310, 126.99020, 2, 0.74, 260.0, 0.85, 15, ["반경 80m 내 2회 이상 회전", "체류 시간 증가"], "잠시 멈춰 서서 주변 가게 간판을 확인하세요.", "동일 구역 15분 이상 선회 중 (경고)"),
        (37.57280, 126.99060, 2, 0.81, 290.0, 0.92, 22, ["반복 선회 및 보행 속도 급감"], "도움이 필요하시면 화면의 통화 버튼을 눌러주세요.", "이상 이동 패턴 지속 (경고)"),
        (37.57300, 126.99010, 3, 0.95, 310.0, 0.98, 30, ["동일 구역 30분 체류 및 원형 배회", "복귀 방향성 상실"], "가까운 가게나 벤치에서 잠시 쉬어주세요. 보호자에게 알렸습니다.", "지속 배회 감지! (익선동 골목 30분 체류, 즉각 확인 필요)")
    ]
    frames_c = []
    for i, (lat, lng, risk, score, dev, ang, stay, reasons, e_alert, g_alert) in enumerate(raw_c):
        t = base_time + timedelta(minutes=i * 6)
        frames_c.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "features": {
                "speed_kmh": 3.0 if risk == 0 else (1.4 if risk < 3 else 0.6),
                "deviation_distance_m": dev,
                "angular_variance": ang,
                "stay_duration_min": stay
            },
            "anomaly_score": score,
            "risk_level": risk,
            "reasons": reasons,
            "elderly_alert": e_alert,
            "guardian_alert": g_alert
        })

    out_dir = "data/synthetic"
    os.makedirs(out_dir, exist_ok=True)

    scenarios = {
        "scenario_normal": {
            "scenario_id": "scenario_normal",
            "title": "시나리오 A: 정상 이동",
            "description": "집에서 서울노인복지센터 방문 후 정상 귀가",
            "target_elderly": "김정순 (만 78세)",
            "frames": frames_a
        },
        "scenario_deviation": {
            "scenario_id": "scenario_deviation",
            "title": "시나리오 B: 일시 이탈 후 복귀",
            "description": "낙원상가 인근 공사로 잠시 우회 후 대로변 복귀",
            "target_elderly": "김정순 (만 78세)",
            "frames": frames_b
        },
        "scenario_wandering": {
            "scenario_id": "scenario_wandering",
            "title": "시나리오 C: 지속 배회",
            "description": "익선동 골목 진입 후 동일 반경 맴돌기 및 복귀 실패",
            "target_elderly": "김정순 (만 78세)",
            "frames": frames_c
        }
    }

    for s_id, s_data in scenarios.items():
        with open(f"{out_dir}/{s_id}.json", "w", encoding="utf-8") as f:
            json.dump(s_data, f, ensure_ascii=False, indent=2)

    with open(f"{out_dir}/all_scenarios.json", "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    print(f" 3개 시나리오 JSON 파일이 '{out_dir}'에 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    generate_dataset()