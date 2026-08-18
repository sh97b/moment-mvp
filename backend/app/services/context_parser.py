"""Gemini 파싱과 결정적 fallback을 API 계약에 맞게 제공한다."""

import os
import re

from backend.app.ai.context.parser import parse_routine_text
from backend.app.models.context import ContextParseResponse, DayCode, WeeklyPattern


DEFAULT_DAYS = [DayCode.TUE, DayCode.THU]
DEFAULT_DESTINATION = "복지관"
DEFAULT_DEPARTURE_TIME = "14:00"
DEFAULT_RETURN_TIME = "18:00"

DAY_ALIASES: tuple[tuple[DayCode, tuple[str, ...]], ...] = (
    (DayCode.MON, ("월요일",)),
    (DayCode.TUE, ("화요일",)),
    (DayCode.WED, ("수요일",)),
    (DayCode.THU, ("목요일",)),
    (DayCode.FRI, ("금요일",)),
    (DayCode.SAT, ("토요일",)),
    (DayCode.SUN, ("일요일",)),
)

# 개인정보나 임의 주소를 응답에 복사하지 않도록 일반적인 합성 장소만 허용한다.
SAFE_DESTINATIONS = (
    "복지관",
    "경로당",
    "주민센터",
    "문화센터",
    "도서관",
    "병원",
    "공원",
    "시장",
    "마트",
    "교회",
    "성당",
    "절",
)

KOREAN_TIME_PATTERN = re.compile(
    r"(?:(오전|오후)\s*)?(\d{1,2})시(?:\s*(\d{1,2})분)?"
)
CLOCK_TIME_PATTERN = re.compile(r"(?<!\d)([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
RETURN_WORDS = ("귀가", "돌아", "복귀")


def _days(text: str) -> list[DayCode]:
    if "매일" in text:
        return [day for day, _aliases in DAY_ALIASES]
    if "평일" in text:
        return [DayCode.MON, DayCode.TUE, DayCode.WED, DayCode.THU, DayCode.FRI]
    if "주말" in text:
        return [DayCode.SAT, DayCode.SUN]
    return [
        day
        for day, aliases in DAY_ALIASES
        if any(alias in text for alias in aliases)
    ]


def _format_korean_time(period: str | None, hour_text: str, minute_text: str | None) -> str | None:
    hour = int(hour_text)
    minute = int(minute_text or 0)
    if minute > 59:
        return None
    if period is not None:
        if not 1 <= hour <= 12:
            return None
        if period == "오전":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
    elif hour > 23:
        return None
    return f"{hour:02d}:{minute:02d}"


def _times(text: str) -> list[tuple[int, int, str]]:
    found: list[tuple[int, int, str]] = []
    for match in KOREAN_TIME_PATTERN.finditer(text):
        value = _format_korean_time(match.group(1), match.group(2), match.group(3))
        if value is not None:
            found.append((match.start(), match.end(), value))
    for match in CLOCK_TIME_PATTERN.finditer(text):
        found.append(
            (match.start(), match.end(), f"{int(match.group(1)):02d}:{int(match.group(2)):02d}")
        )
    return sorted(found, key=lambda item: item[0])


def parse_context_fallback(text: str) -> ContextParseResponse:
    """입력 원문을 보관하지 않고 매 호출마다 같은 규칙으로 결과를 만든다."""

    warnings = ["Gemini를 사용하지 않고 규칙 기반 fallback으로 처리했습니다."]

    days = _days(text)
    if not days:
        days = DEFAULT_DAYS.copy()
        warnings.append("요일을 인식하지 못해 합성 기본 요일을 사용했습니다.")

    destination = next(
        (candidate for candidate in SAFE_DESTINATIONS if candidate in text),
        None,
    )
    if destination is None:
        destination = DEFAULT_DESTINATION
        warnings.append("목적지를 인식하지 못해 합성 기본 목적지를 사용했습니다.")

    found_times = _times(text)
    departure_time = DEFAULT_DEPARTURE_TIME
    return_time = DEFAULT_RETURN_TIME
    if len(found_times) >= 2:
        departure_time = found_times[0][2]
        return_time = found_times[1][2]
    elif len(found_times) == 1:
        start, end, value = found_times[0]
        nearby_text = text[max(0, start - 6) : min(len(text), end + 12)]
        if any(word in nearby_text for word in RETURN_WORDS):
            return_time = value
            warnings.append("출발 시간을 인식하지 못해 합성 기본값을 사용했습니다.")
        else:
            departure_time = value
            warnings.append("귀가 시간을 인식하지 못해 합성 기본값을 사용했습니다.")
    else:
        warnings.append("시간을 인식하지 못해 합성 기본 시간을 사용했습니다.")

    return ContextParseResponse(
        weekly_patterns=[
            WeeklyPattern(
                days=days,
                destination=destination,
                departure_time=departure_time,
                return_time=return_time,
            )
        ],
        source="fallback",
        warnings=warnings,
    )


def parse_context_with_fallback(text: str) -> ContextParseResponse:
    """Gemini가 없거나 결과가 계약에 맞지 않으면 기존 fallback을 사용한다."""

    if not os.getenv("GEMINI_API_KEY"):
        return parse_context_fallback(text)

    try:
        parsed = parse_routine_text(text)
        if not parsed.routines:
            raise ValueError("Gemini가 생활패턴을 반환하지 않았습니다.")
        return ContextParseResponse(
            weekly_patterns=[
                WeeklyPattern(
                    days=routine.days,
                    destination=routine.destination,
                    departure_time=routine.time,
                    return_time=routine.return_time,
                )
                for routine in parsed.routines
            ],
            source="gemini",
            warnings=[],
        )
    except Exception:
        return parse_context_fallback(text)
