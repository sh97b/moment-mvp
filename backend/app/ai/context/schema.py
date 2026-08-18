from typing import Literal

from pydantic import BaseModel, Field


DayCode = Literal[
    "MON",
    "TUE",
    "WED",
    "THU",
    "FRI",
    "SAT",
    "SUN",
]


# =========================================
# Gemini가 추출하는 하나의 생활 루틴
# =========================================

class Routine(BaseModel):
    days: list[DayCode] = Field(
        default_factory=list,
        description="활동이 반복되는 요일 목록",
    )

    time: str | None = Field(
        default=None,
        description=(
            "구체적인 활동 시각. "
            "알 수 있으면 HH:MM, "
            "알 수 없으면 null"
        ),
    )

    time_period: str | None = Field(
        default=None,
        description=(
            "오전, 오후, 아침, 저녁처럼 "
            "정확한 시각 대신 사용된 시간대 표현"
        ),
    )

    time_is_approximate: bool = Field(
        default=False,
        description=(
            "'2시쯤'처럼 정확하지 않은 "
            "시간 표현이면 true"
        ),
    )

    destination: str | None = Field(
        default=None,
        description=(
            "복지관, 병원, 공원 등 목적지. "
            "명시되지 않으면 null"
        ),
    )

    activity: str = Field(
        description=(
            "산책, 복지관 방문, 병원 진료 등 "
            "사용자가 하는 활동"
        ),
    )


# =========================================
# Gemini가 반환하는 결과
# =========================================

class ParsedRoutineContext(BaseModel):
    routines: list[Routine] = Field(
        default_factory=list,
    )


# =========================================
# 초기 설정 전체 Context
# =========================================

class InitialContext(BaseModel):
    person_name: str

    home_location: str

    frequent_places: list[str]

    usual_return_time: str

    routines: list[Routine]