"""생활패턴 파싱 API의 공개 요청·응답 모델을 정의한다."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr


MAX_CONTEXT_TEXT_LENGTH = 1000
TIME_PATTERN = r"^(?:[01]\d|2[0-3]):[0-5]\d$"


class DayCode(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"


class ContextParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: StrictStr = Field(max_length=MAX_CONTEXT_TEXT_LENGTH)


class WeeklyPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: list[DayCode] = Field(min_length=1)
    destination: str = Field(min_length=1, max_length=50)
    departure_time: str = Field(pattern=TIME_PATTERN)
    return_time: str = Field(pattern=TIME_PATTERN)


class ContextParseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekly_patterns: list[WeeklyPattern]
    source: Literal["gemini", "fallback"]
    warnings: list[str]
