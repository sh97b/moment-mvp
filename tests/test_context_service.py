from backend.app.ai.context.schema import (
    ParsedRoutineContext,
    Routine,
)
from backend.app.ai.context.service import (
    build_initial_context,
)


def test_build_initial_context(monkeypatch):
    fake_parsed = ParsedRoutineContext(
        routines=[
            Routine(
                days=["TUE", "THU"],
                time="14:00",
                time_period="오후",
                time_is_approximate=True,
                destination="복지관",
                activity="복지관 방문",
            )
        ]
    )

    def mock_parse_routine_text(routine_text):
        return fake_parsed

    monkeypatch.setattr(
        "backend.app.ai.context.service.parse_routine_text",
        mock_parse_routine_text,
    )

    result = build_initial_context(
        person_name="공나영",
        home_location="서울시 강북구 수유동 123",
        frequent_places=[
            "강북구청 경로당",
            "수유근린공원",
        ],
        usual_return_time="18:00",
        routine_text=(
            "화요일과 목요일 오후 2시쯤 "
            "복지관에 방문합니다."
        ),
    )

    assert result.person_name == "공나영"
    assert result.home_location == "서울시 강북구 수유동 123"
    assert result.frequent_places == [
        "강북구청 경로당",
        "수유근린공원",
    ]
    assert result.usual_return_time == "18:00"

    assert len(result.routines) == 1

    routine = result.routines[0]

    assert routine.days == ["TUE", "THU"]
    assert routine.time == "14:00"
    assert routine.destination == "복지관"
    assert routine.activity == "복지관 방문"


def test_parse_context_response_matches_api_contract(
    monkeypatch,
):
    from backend.app.ai.context.schema import (
        ParsedRoutineContext,
        Routine,
    )
    from backend.app.ai.context.service import (
        parse_context_response,
    )

    fake_parsed = ParsedRoutineContext(
        routines=[
            Routine(
                days=["TUE", "THU"],
                time="14:00",
                return_time="18:00",
                time_period="오후",
                time_is_approximate=False,
                destination="복지관",
                activity="복지관 방문",
            )
        ]
    )

    def mock_parse_routine_text(text):
        return fake_parsed

    monkeypatch.setattr(
        "backend.app.ai.context.service.parse_routine_text",
        mock_parse_routine_text,
    )

    result = parse_context_response(
        "화요일과 목요일 오후 2시에 복지관에 가고 "
        "보통 오후 6시 전에 귀가해요."
    )

    assert result.source == "gemini"
    assert result.warnings == []

    assert len(result.weekly_patterns) == 1

    pattern = result.weekly_patterns[0]

    assert pattern.days == ["TUE", "THU"]
    assert pattern.destination == "복지관"
    assert pattern.departure_time == "14:00"
    assert pattern.return_time == "18:00"


def test_parse_context_response_uses_fallback_on_gemini_failure(
    monkeypatch,
):
    from backend.app.ai.context.service import (
        parse_context_response,
    )

    def mock_parse_routine_text(text):
        raise RuntimeError(
            "Gemini 생활패턴 파싱에 실패했습니다. status=503"
        )

    monkeypatch.setattr(
        "backend.app.ai.context.service.parse_routine_text",
        mock_parse_routine_text,
    )

    result = parse_context_response(
        "화요일과 목요일 오후 2시에 복지관에 가요."
    )

    assert result.source == "fallback"
    assert result.weekly_patterns == []
    assert len(result.warnings) == 1

    assert (
        "Gemini 생활패턴 파싱을 사용할 수 없습니다"
        in result.warnings[0]
    )