"""Gemini structured output으로 생활패턴 문장을 파싱한다."""

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from backend.app.models.context import DayCode
from backend.app.ai.context.prompts import ROUTINE_PARSE_PROMPT


MODEL_NAME = "gemini-3.6-flash"


class Routine(BaseModel):
    days: list[DayCode] = Field(default_factory=list)
    time: str | None = None
    return_time: str | None = None
    time_period: str | None = None
    time_is_approximate: bool = False
    destination: str | None = None
    activity: str


class ParsedRoutineContext(BaseModel):
    routines: list[Routine] = Field(default_factory=list)


def parse_routine_text(routine_text: str) -> ParsedRoutineContext:
    """Gemini가 반환한 structured output을 내부 routine 모델로 검증한다."""

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"{ROUTINE_PARSE_PROMPT}\n\n사용자 입력:\n{routine_text}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParsedRoutineContext,
                temperature=0,
            ),
        )
    except errors.APIError as exc:
        raise RuntimeError("Gemini API 호출에 실패했습니다.") from exc
    except ValueError as exc:
        raise RuntimeError("Gemini API 설정이 올바르지 않습니다.") from exc

    if response.parsed is None:
        raise ValueError("Gemini structured output이 비어 있습니다.")
    return ParsedRoutineContext.model_validate(response.parsed)
