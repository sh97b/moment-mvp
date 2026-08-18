import json

from fastapi.testclient import TestClient

from backend.app.main import _cors_origins, app
from backend.app.models.replay import ReplayResponse
from backend.app.services.replay_service import ReplayService
from backend.app.services.scenario_loader import ScenarioLoader


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "moment-api"
    assert set(response.json()) == {
        "status",
        "service",
        "model_ready",
        "gemini_available",
        "mock_fallback_available",
    }


def test_context_parse_fallback_matches_contract_and_is_deterministic() -> None:
    request = {
        "text": "화요일과 목요일 오후 2시에 복지관에 가고 보통 오후 6시 전에 귀가해요."
    }

    first = client.post("/api/context/parse", json=request)
    second = client.post("/api/context/parse", json=request)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["weekly_patterns"] == [
        {
            "days": ["TUE", "THU"],
            "destination": "복지관",
            "departure_time": "14:00",
            "return_time": "18:00",
        }
    ]
    assert first.json()["source"] == "fallback"
    assert first.json()["warnings"]
    assert set(first.json()) == {"weekly_patterns", "source", "warnings"}


def test_context_parse_rejects_empty_or_whitespace_text() -> None:
    for text in ("", "   \t\n"):
        response = client.post("/api/context/parse", json={"text": text})
        assert response.status_code == 422
        assert response.json() == {"detail": "생활패턴 입력이 비어 있습니다."}


def test_context_parse_rejects_invalid_requests_and_long_input() -> None:
    for body in ({}, {"text": 123}, {"text": "정상 입력", "extra": True}):
        response = client.post("/api/context/parse", json=body)
        assert response.status_code == 422

    response = client.post("/api/context/parse", json={"text": "가" * 1001})
    assert response.status_code == 422


def test_context_parse_does_not_echo_unrecognized_personal_details() -> None:
    private_text = "홍길동은 서울시 종로구 123번지에서 매일 오전 9시에 외출합니다."
    response = client.post("/api/context/parse", json={"text": private_text})
    assert response.status_code == 200
    assert "홍길동" not in response.text
    assert "123번지" not in response.text


def test_scenarios_match_contract() -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["scenarios"]] == [
        "normal",
        "temporary_return",
        "persistent_anomaly",
    ]
    assert all(set(item) == {"id", "name", "description"} for item in response.json()["scenarios"])


def test_normal_replay_is_ordered_valid_and_stays_normal() -> None:
    response = client.get("/api/replay/normal")
    assert response.status_code == 200
    replay = ReplayResponse.model_validate(response.json())
    assert replay.frames
    assert [frame.timestamp for frame in replay.frames] == sorted(
        frame.timestamp for frame in replay.frames
    )
    assert {frame.risk_level for frame in replay.frames} == {0}
    assert set(response.json()) == {"scenario_id", "interval_ms", "frames"}
    assert set(response.json()["frames"][0]) == {
        "timestamp",
        "lat",
        "lng",
        "features",
        "anomaly_score",
        "risk_level",
        "reasons",
        "elderly_alert",
        "guardian_alert",
    }
    assert set(response.json()["frames"][0]["features"]) == {
        "turn_count",
        "revisit_count",
        "home_distance_m",
        "home_distance_delta_m",
    }


def test_scenario_risk_transitions() -> None:
    temporary = client.get("/api/replay/temporary_return").json()["frames"]
    persistent = client.get("/api/replay/persistent_anomaly").json()["frames"]
    assert [frame["risk_level"] for frame in temporary] == [0, 1, 1, 0]
    assert [frame["risk_level"] for frame in persistent] == [0, 1, 2, 3]
    assert all(0 <= frame["risk_level"] <= 3 for frame in temporary + persistent)
    assert persistent[-1]["reasons"]


def test_unknown_scenario_is_404() -> None:
    response = client.get("/api/replay/not-a-scenario")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown scenario_id"}


def test_cors_preflight() -> None:
    response = client.options(
        "/api/replay/normal",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_empty_or_invalid_cors_config_uses_demo_defaults(monkeypatch) -> None:
    for configured in ("", "not-an-origin", "http://[bad", " , "):
        monkeypatch.setenv("CORS_ORIGINS", configured)
        assert _cors_origins() == [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]


def test_repeated_request_has_no_state_leak() -> None:
    first = client.get("/api/replay/persistent_anomaly")
    second = client.get("/api/replay/persistent_anomaly")
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


def test_bad_json_returns_controlled_error(tmp_path) -> None:
    (tmp_path / "normal.json").write_text("{broken", encoding="utf-8")
    service_loader = ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    from backend.app import main

    saved = main.replay_service
    main.replay_service = ReplayService(service_loader)
    try:
        response = client.get("/api/replay/normal")
    finally:
        main.replay_service = saved
    assert response.status_code == 422
    assert response.json() == {"detail": "Scenario data is not valid JSON"}


def test_missing_features_returns_controlled_error_without_internal_path(tmp_path) -> None:
    invalid = {
        "frames": [
            {
                "timestamp": "2026-08-18T14:00:00+09:00",
                "lat": 37.5,
                "lng": 126.9,
            }
        ]
    }
    (tmp_path / "normal.json").write_text(json.dumps(invalid), encoding="utf-8")
    from backend.app import main

    saved = main.replay_service
    main.replay_service = ReplayService(
        ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    )
    try:
        response = client.get("/api/replay/normal")
    finally:
        main.replay_service = saved
    assert response.status_code == 422
    assert response.json() == {"detail": "Scenario frame validation failed"}
    assert str(tmp_path) not in response.text


def test_missing_data_returns_controlled_error(tmp_path) -> None:
    from backend.app import main

    saved = main.replay_service
    main.replay_service = ReplayService(
        ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    )
    try:
        response = client.get("/api/replay/normal")
    finally:
        main.replay_service = saved
    assert response.status_code == 503
    assert response.json() == {"detail": "Scenario data is temporarily unavailable"}


def test_empty_frames_are_valid(tmp_path) -> None:
    (tmp_path / "normal.json").write_text(json.dumps({"frames": []}), encoding="utf-8")
    replay = ReplayService(
        ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    ).build_replay("normal")
    assert replay.frames == []


def test_invalid_coordinate_and_timestamp_are_rejected(tmp_path) -> None:
    invalid = {
        "frames": [
            {
                "timestamp": "2026-08-18T14:00:00",
                "lat": 120,
                "lng": 126.9,
                "features": {},
            }
        ]
    }
    (tmp_path / "normal.json").write_text(json.dumps(invalid), encoding="utf-8")
    loader = ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    from backend.app.services.scenario_loader import ScenarioDataError

    try:
        loader.load("normal")
    except ScenarioDataError as exc:
        assert str(exc) == "Scenario frame validation failed"
    else:
        raise AssertionError("invalid frame was accepted")


def test_missing_field_and_non_finite_json_are_rejected(tmp_path) -> None:
    missing = {
        "frames": [
            {
                "timestamp": "2026-08-18T14:00:00+09:00",
                "lat": 37.5,
                "features": {},
            }
        ]
    }
    (tmp_path / "normal.json").write_text(json.dumps(missing), encoding="utf-8")
    loader = ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    from backend.app.services.scenario_loader import ScenarioDataError

    try:
        loader.load("normal")
    except ScenarioDataError:
        pass
    else:
        raise AssertionError("frame with a missing required field was accepted")

    (tmp_path / "normal.json").write_text(
        '{"frames":[{"timestamp":"2026-08-18T14:00:00+09:00",'
        '"lat":NaN,"lng":126.9,"features":{}}]}',
        encoding="utf-8",
    )
    try:
        loader.load("normal")
    except ScenarioDataError as exc:
        assert str(exc) == "Scenario data is not valid JSON"
    else:
        raise AssertionError("non-finite JSON was accepted")

    (tmp_path / "normal.json").write_text(
        '{"frames":[{"timestamp":"2026-08-18T14:00:00+09:00",'
        '"lat":37.5,"lng":126.9,"features":{"future_metric":1e400}}]}',
        encoding="utf-8",
    )
    try:
        loader.load("normal")
    except ScenarioDataError:
        pass
    else:
        raise AssertionError("non-finite extra feature was accepted")


def test_loader_sorts_out_of_order_frames(tmp_path) -> None:
    frames = [
        {"timestamp": "2026-08-18T14:02:00+09:00", "lat": 37.5, "lng": 126.9, "features": {}},
        {"timestamp": "2026-08-18T14:01:00+09:00", "lat": 37.5, "lng": 126.9, "features": {}},
    ]
    (tmp_path / "normal.json").write_text(
        json.dumps({"frames": frames}), encoding="utf-8"
    )
    loaded = ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path).load("normal")
    assert loaded[0].timestamp < loaded[1].timestamp


def test_primary_data_has_priority_over_fixture(tmp_path) -> None:
    primary = tmp_path / "primary"
    fallback = tmp_path / "fallback"
    primary.mkdir()
    fallback.mkdir()
    frame = {
        "timestamp": "2026-08-18T14:00:00+09:00",
        "lat": 37.5,
        "lng": 126.9,
        "features": {},
    }
    (primary / "normal.json").write_text(
        json.dumps({"frames": [frame]}), encoding="utf-8"
    )
    frame["lat"] = 38.5
    (fallback / "normal.json").write_text(
        json.dumps({"frames": [frame]}), encoding="utf-8"
    )
    loaded = ScenarioLoader(data_dir=primary, fallback_dir=fallback).load("normal")
    assert loaded[0].lat == 37.5


def test_safety_loop_runs_after_timestamp_sort(tmp_path) -> None:
    chronological = [
        {
            "timestamp": f"2026-08-18T14:0{minute}:00+09:00",
            "lat": 37.5,
            "lng": 126.9,
            "features": features,
            "anomaly_score": score,
            "is_anomaly": anomaly,
        }
        for minute, features, score, anomaly in [
            (0, {}, 0.1, False),
            (1, {"distance_from_route_m": 100}, 0.7, True),
            (2, {"distance_from_route_m": 120, "turn_count": 5}, 0.8, True),
            (3, {"distance_from_route_m": 150, "turn_count": 6, "revisit_count": 2, "home_distance_delta_m": 50}, 0.9, True),
        ]
    ]
    (tmp_path / "persistent_anomaly.json").write_text(
        json.dumps({"frames": list(reversed(chronological))}), encoding="utf-8"
    )
    replay = ReplayService(
        ScenarioLoader(data_dir=tmp_path, fallback_dir=tmp_path)
    ).build_replay("persistent_anomaly")
    assert [frame.risk_level for frame in replay.frames] == [0, 1, 2, 3]


def test_model_failure_and_invalid_output_use_rule_fallback() -> None:
    def failed_predictor(_features):
        raise RuntimeError("model unavailable")

    service = ReplayService(ScenarioLoader(), predictor=failed_predictor)
    replay = service.build_replay("persistent_anomaly")
    assert [frame.risk_level for frame in replay.frames] == [0, 1, 2, 3]
    assert all(0 <= frame.anomaly_score <= 1 for frame in replay.frames)

    invalid = ReplayService(
        ScenarioLoader(),
        predictor=lambda _features: {"anomaly_score": float("nan")},
    ).build_replay("normal")
    assert all(frame.anomaly_score == 0 for frame in invalid.frames)

    missing_flag = ReplayService(
        ScenarioLoader(), predictor=lambda _features: {"anomaly_score": 0.99}
    ).build_replay("normal")
    assert all(frame.risk_level == 0 for frame in missing_flag.frames)
    assert all(frame.anomaly_score == 0 for frame in missing_flag.frames)

    boolean_score = ReplayService(
        ScenarioLoader(),
        predictor=lambda _features: {"anomaly_score": True, "is_anomaly": True},
    ).build_replay("normal")
    assert all(frame.risk_level == 0 for frame in boolean_score.frames)
    assert all(frame.anomaly_score == 0 for frame in boolean_score.frames)
