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