import json
import os
from datetime import datetime, timedelta

def generate_dataset():
    base_time = datetime(2026, 8, 18, 14, 0, 0)
    
    # -------------------------------------------------------------
    # Scenario A: 정상 이동 (종로3가 집 -> 서울노인복지센터 -> 집)
    # -------------------------------------------------------------
    # (lat, lng, 턴수, 재방문, 반복구간, 반경체류분, 집거리추세)
    movement_a = [
        (37.57182, 126.98921, 0, 0, 0, 0, "유지"),
        (37.57245, 126.98860, 0, 0, 0, 0, "증가"),
        (37.57350, 126.98750, 1, 0, 0, 0, "증가"),
        (37.57460, 126.98630, 1, 0, 0, 0, "증가"),
        (37.57520, 126.98580, 2, 0, 0, 0, "유지"), # 도착
        (37.57460, 126.98630, 2, 0, 1, 0, "감소"),
        (37.57350, 126.98750, 3, 0, 1, 0, "감소"),
        (37.57182, 126.98921, 3, 0, 1, 0, "감소")  # 귀가
    ]
    
    frames_a = []
    for i, (lat, lng, turn, rev, rep, stay_rad, trend) in enumerate(movement_a):
        t = base_time + timedelta(minutes=i * 4)
        frames_a.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "personal_lifestyle_features": {
                "outing_duration_hr": round(i * 4 / 60, 2),
                "total_distance_m": round(i * 120.0, 1),
                "max_deviation_from_home_m": 12.0,
                "return_time_diff_min": 0,
                "stay_outside_living_area_min": 0
            },
            "realtime_movement_features": {
                "turn_count": turn,
                "revisit_count": rev,
                "repeat_section": rep,
                "radius_stay_duration_min": stay_rad,
                "home_distance_trend": trend
            },
            "anomaly_score": 0.03,
            "risk_level": 0,
            "reasons": [],
            "elderly_alert": "안전한 경로로 이동 중입니다.",
            "guardian_alert": "정상 이동 중 (목적지: 서울노인복지센터)"
        })

    # -------------------------------------------------------------
    # Scenario B: 일시 우회 후 귀가
    # -------------------------------------------------------------
    raw_b = [
        (37.57520, 126.98580, 2, 0, 0, 0, "유지", 0, 0.04, [], None, None),
        (37.57460, 126.98630, 2, 0, 1, 0, "감소", 0, 0.08, [], None, None),
        # 우회 발생
        (37.57380, 126.98820, 5, 0, 0, 4, "증가", 1, 0.58, ["방향전환 횟수 일시 증가", "집과의 거리 일시 증가"], "평소 다니시던 길이 아닙니다. 큰길 방향을 확인하세요.", "일시적 경로 우회 감지 (주의 관찰)"),
        (37.57310, 126.98890, 7, 1, 0, 6, "유지", 1, 0.62, ["우회 경로 지속"], "종로3가역 큰길 방향으로 이동해 주세요.", "일시적 우회 지속"),
        # 복귀
        (37.57245, 126.98860, 8, 1, 1, 0, "감소", 0, 0.12, ["정상 경로로 복귀함"], "정상 경로로 복귀하셨습니다.", "정상 경로 복귀 확인 (주의 해제)"),
        (37.57182, 126.98921, 9, 1, 1, 0, "감소", 0, 0.03, [], "집에 도착하셨습니다.", "안전 귀가 완료")
    ]
    
    frames_b = []
    for i, (lat, lng, turn, rev, rep, stay_rad, trend, risk, score, reasons, e_alert, g_alert) in enumerate(raw_b):
        t = base_time + timedelta(minutes=i * 4)
        frames_b.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "personal_lifestyle_features": {
                "outing_duration_hr": round(0.5 + (i * 4 / 60), 2),
                "total_distance_m": round(500.0 + (i * 110.0), 1),
                "max_deviation_from_home_m": 165.0 if risk == 1 else 15.0,
                "return_time_diff_min": 10 if risk == 1 else 0,
                "stay_outside_living_area_min": 5 if risk == 1 else 0
            },
            "realtime_movement_features": {
                "turn_count": turn,
                "revisit_count": rev,
                "repeat_section": rep,
                "radius_stay_duration_min": stay_rad,
                "home_distance_trend": trend
            },
            "anomaly_score": score,
            "risk_level": risk,
            "reasons": reasons,
            "elderly_alert": e_alert,
            "guardian_alert": g_alert
        })

    # -------------------------------------------------------------
    # Scenario C: 지속 배회 (이동 형태 이상 복합 발생)
    # -------------------------------------------------------------
    raw_c = [
        (37.57520, 126.98580, 2, 0, 0, 0, "유지", 0, 0.04, [], None, None),
        # 1단계 주의
        (37.57390, 126.98910, 5, 1, 0, 5, "증가", 1, 0.52, ["방향전환 급증", "집과의 거리 지속 증가"], "가시는 곳을 다시 확인해 보세요.", "경로 이탈 및 방황 조짐 감지"),
        # 2단계 경고: 익선동 좁은 골목 맴돌기
        (37.57310, 126.99020, 11, 2, 1, 15, "증가", 2, 0.74, ["반경 80m 내 15분 체류", "동일 지점 2회 재방문"], "잠시 멈춰 서서 주변 가게 간판을 확인하세요.", "동일 구역 15분 이상 선회 중 (경고)"),
        (37.57280, 126.99060, 16, 3, 2, 22, "유지", 2, 0.81, ["동일 구간 반복 보행", "반경 체류 22분 초과"], "도움이 필요하시면 화면의 통화 버튼을 눌러주세요.", "이상 이동 패턴 지속 (경고)"),
        # 3단계 위험: 방향성 완전 상실
        (37.57300, 126.99010, 22, 4, 3, 30, "증가", 3, 0.95, ["반경 100m 내 30분 이상 배회", "방향전환 20회 초과 및 귀가 실패"], "가까운 가게나 벤치에서 잠시 쉬어주세요. 보호자에게 알렸습니다.", "지속 배회 감지! (익선동 골목 30분 체류, 즉각 확인 필요)")
    ]
    
    frames_c = []
    for i, (lat, lng, turn, rev, rep, stay_rad, trend, risk, score, reasons, e_alert, g_alert) in enumerate(raw_c):
        t = base_time + timedelta(minutes=i * 6)
        frames_c.append({
            "frame_id": i + 1,
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "personal_lifestyle_features": {
                "outing_duration_hr": round(0.5 + (i * 6 / 60), 2),
                "total_distance_m": round(500.0 + (i * 90.0), 1),
                "max_deviation_from_home_m": 310.0 if risk == 3 else (260.0 if risk == 2 else 140.0),
                "return_time_diff_min": i * 15,
                "stay_outside_living_area_min": i * 6
            },
            "realtime_movement_features": {
                "turn_count": turn,
                "revisit_count": rev,
                "repeat_section": rep,
                "radius_stay_duration_min": stay_rad,
                "home_distance_trend": trend
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
            "title": "시나리오 B: 일시 우회 후 귀가",
            "description": "낙원상가 인근 골목 우회 후 큰길 복귀",
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

    print(f"시나리오 JSON 생성 완료: {out_dir}")

if __name__ == "__main__":
    generate_dataset()