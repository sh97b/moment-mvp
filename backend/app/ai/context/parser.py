from google import genai
from google.genai import types

from backend.app.ai.context.prompts import (
    ROUTINE_PARSE_PROMPT,
)

from backend.app.ai.context.schema import (
    ParsedRoutineContext,
)


# =========================================
# Gemini 모델
# =========================================

MODEL_NAME = "gemini-3.6-flash"


# =========================================
# Gemini Client
# =========================================

client = genai.Client()


# =========================================
# 생활패턴 자연어 파싱
# =========================================

def parse_routine_text(
    routine_text: str,
) -> ParsedRoutineContext:
    """
    사용자가 입력한 자연어 생활패턴을
    구조화된 ParsedRoutineContext로 변환한다.
    """

    # -------------------------------------
    # 1. 입력 검증
    # -------------------------------------

    routine_text = routine_text.strip()

    if not routine_text:
        return ParsedRoutineContext(
            routines=[]
        )


    # -------------------------------------
    # 2. Gemini에 전달할 입력 구성
    # -------------------------------------

    user_prompt = f"""
{ROUTINE_PARSE_PROMPT}

사용자 입력:
{routine_text}
"""


    # -------------------------------------
    # 3. Gemini 호출
    # -------------------------------------

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ParsedRoutineContext,
            temperature=0,
        ),
    )


    # -------------------------------------
    # 4. Structured Output 확인
    # -------------------------------------

    if response.parsed is None:
        raise ValueError(
            "Gemini가 생활패턴을 "
            "구조화하지 못했습니다."
        )


    # -------------------------------------
    # 5. Pydantic 객체 반환
    # -------------------------------------

    return response.parsed