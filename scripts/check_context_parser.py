from backend.app.ai.context.parser import parse_routine_text


def main():
    routine_text = (
        "화요일과 목요일 오후 2시쯤 복지관에 방문하고, "
        "평일에는 오전 산책을 자주 합니다."
    )

    result = parse_routine_text(routine_text)

    print("=== Gemini 생활패턴 파싱 결과 ===")
    print(
        result.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()