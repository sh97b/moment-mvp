from backend.app.ai.context.schema import (
    InitialContext,
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