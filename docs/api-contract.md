# MOMENT MVP API Contract

프론트엔드와 백엔드는 이 문서를 공통 계약으로 사용합니다. 필드명이나 타입을 변경하려면 팀장 확인 후 이 문서와 mock JSON을 먼저 함께 수정합니다.

## Common rules

- Base URL: `http://localhost:8000`
- Content type: `application/json`
- Timestamp: ISO 8601 string with timezone
- Coordinates: decimal degrees (`lat`, `lng`)
- Risk level: integer `0 | 1 | 2 | 3`
- All demo data must be synthetic.

## `GET /api/health`

### Response `200`

```json
{
  "status": "ok",
  "service": "moment-api",
  "model_ready": true,
  "gemini_available": true,
  "mock_fallback_available": true
}
```

The service may return `gemini_available: false` while remaining healthy because local fallback data is required.

## `POST /api/context/parse`

Natural-language living patterns are converted to a fixed JSON structure. Gemini is used only for this endpoint.

### Request

```json
{
  "text": "화요일과 목요일 오후 2시에 복지관에 가고 보통 오후 6시 전에 귀가해요."
}
```

### Response `200`

```json
{
  "weekly_patterns": [
    {
      "days": ["TUE", "THU"],
      "destination": "복지관",
      "departure_time": "14:00",
      "return_time": "18:00"
    }
  ],
  "source": "gemini",
  "warnings": []
}
```

When Gemini is unavailable or returns invalid JSON, return the same schema with `source: "fallback"` and a warning. Do not fail the entire demo.

### Error `422`

```json
{
  "detail": "생활패턴 입력이 비어 있습니다."
}
```

## `GET /api/scenarios`

### Response `200`

```json
{
  "scenarios": [
    {
      "id": "normal",
      "name": "정상 이동",
      "description": "평소 경로를 따라 목적지에 다녀옵니다."
    },
    {
      "id": "temporary_return",
      "name": "일시 이탈 후 복귀",
      "description": "경로를 잠시 벗어나지만 안내 후 정상 경로로 복귀합니다."
    },
    {
      "id": "persistent_anomaly",
      "name": "이상 이동 지속",
      "description": "반복 이동과 방향 전환이 지속되고 집과의 거리가 증가합니다."
    }
  ]
}
```

## `GET /api/replay/{scenario_id}`

Return the entire ordered frame array at once. The frontend replays it with a timer.

### Response `200`

```json
{
  "scenario_id": "temporary_return",
  "interval_ms": 1000,
  "frames": [
    {
      "timestamp": "2026-08-18T14:00:00+09:00",
      "lat": 37.5665,
      "lng": 126.9780,
      "features": {
        "turn_count": 1,
        "revisit_count": 0,
        "home_distance_m": 320.4,
        "home_distance_delta_m": 18.2
      },
      "anomaly_score": 0.18,
      "risk_level": 0,
      "reasons": [],
      "elderly_alert": null,
      "guardian_alert": null
    },
    {
      "timestamp": "2026-08-18T14:01:00+09:00",
      "lat": 37.5668,
      "lng": 126.9785,
      "features": {
        "turn_count": 3,
        "revisit_count": 1,
        "home_distance_m": 361.7,
        "home_distance_delta_m": 41.3
      },
      "anomaly_score": 0.72,
      "risk_level": 1,
      "reasons": ["최근 구간의 방향 전환이 평소보다 많습니다."],
      "elderly_alert": {
        "title": "잠시 경로를 확인해 주세요",
        "message": "평소 이동 경로와 조금 달라요. 익숙한 길로 돌아가 볼까요?"
      },
      "guardian_alert": null
    }
  ]
}
```

### Error `404`

```json
{
  "detail": "Unknown scenario_id"
}
```

## Risk transition rules

- Level 0: no abnormal feature and no sustained model signal
- Level 1: one abnormal feature or a single threshold crossing; notify the senior only
- Level 2: two or more abnormal features persist for two consecutive frames; show guardian warning
- Level 3: abnormal movement continues after senior guidance and distance from home increases; request guardian intervention
- Downshift: destination/home distance decreases for two consecutive frames and abnormal features ease

`anomaly_score` is a normalized UI risk value where larger means more abnormal. The backend must test any conversion from Isolation Forest `decision_function` so the sign is not reversed.

## Compatibility rule

Frontend mock data and backend responses must conform to this contract. Additive optional fields are allowed only after coordination; do not rename or remove existing fields during the hackathon.

