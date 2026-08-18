import pytest

from google.genai import errors

from backend.app.ai.context import parser


def test_parse_routine_text_handles_gemini_api_error(
    monkeypatch,
):
    class FakeModels:
        def generate_content(
            self,
            *args,
            **kwargs,
        ):
            raise errors.ServerError(
                503,
                {
                    "error": {
                        "code": 503,
                        "message": "high demand",
                        "status": "UNAVAILABLE",
                    }
                },
                None,
            )

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    monkeypatch.setattr(
        parser.genai,
        "Client",
        FakeClient,
    )

    with pytest.raises(
        RuntimeError,
        match="status=503",
    ):
        parser.parse_routine_text(
            "평일 오전에 산책을 합니다."
        )



def test_parse_routine_text_handles_missing_api_key(
        monkeypatch,
    ):
        def mock_client():
            raise ValueError("API key missing")

        monkeypatch.setattr(
            parser.genai,
            "Client",
            mock_client,
        )

        with pytest.raises(
            RuntimeError,
            match="GEMINI_API_KEY",
        ):
            parser.parse_routine_text(
                "평일 오전에 산책을 합니다."
            )   


def test_parse_routine_text_returns_parsed_context(
    monkeypatch,
):
    from backend.app.ai.context.schema import (
        ParsedRoutineContext,
        Routine,
    )

    fake_result = ParsedRoutineContext(
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

    class FakeResponse:
        parsed = fake_result

    class FakeModels:
        def generate_content(
            self,
            *args,
            **kwargs,
        ):
            return FakeResponse()

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    monkeypatch.setattr(
        parser.genai,
        "Client",
        FakeClient,
    )

    result = parser.parse_routine_text(
        "화요일과 목요일 오후 2시쯤 "
        "복지관에 방문합니다."
    )

    assert len(result.routines) == 1

    routine = result.routines[0]

    assert routine.days == ["TUE", "THU"]
    assert routine.time == "14:00"
    assert routine.time_period == "오후"
    assert routine.time_is_approximate is True
    assert routine.destination == "복지관"
    assert routine.activity == "복지관 방문"