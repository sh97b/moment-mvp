from backend.app.ai.context.schema import (
    InitialContext,
    ContextParseResponse,
    WeeklyPattern,
)
from backend.app.ai.context.parser import (
    parse_routine_text,
)

def build_initial_context(
    person_name: str,
    home_location: str,
    frequent_places: list[str],
    usual_return_time: str,
    routine_text: str,
) -> InitialContext:
    """
    초기 설정 화면에서 받은 값과
    Gemini가 파싱한 생활패턴을 합쳐
    최종 InitialContext를 만든다.
    """

    parsed = parse_routine_text(routine_text)

    return InitialContext(
        person_name=person_name,
        home_location=home_location,
        frequent_places=frequent_places,
        usual_return_time=usual_return_time,
        routines=parsed.routines,
    )


def parse_context_response(
    text: str,
) -> ContextParseResponse:
    """
    자연어 생활패턴을 API Contract 형식으로 변환한다.

    Gemini 호출이 실패하거나 결과가 유효하지 않으면
    같은 응답 스키마의 fallback 결과를 반환한다.
    """

    try:
        parsed = parse_routine_text(text)

        weekly_patterns = [
            WeeklyPattern(
                days=routine.days,
                destination=routine.destination,
                departure_time=routine.time,
                return_time=routine.return_time,
            )
            for routine in parsed.routines
        ]

        return ContextParseResponse(
            weekly_patterns=weekly_patterns,
            source="gemini",
            warnings=[],
        )

    except (RuntimeError, ValueError) as e:
        return ContextParseResponse(
            weekly_patterns=[],
            source="fallback",
            warnings=[
                f"Gemini 생활패턴 파싱을 사용할 수 없습니다: {e}"
            ],
        )