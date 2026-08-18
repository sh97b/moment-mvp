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