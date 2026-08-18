from backend.app.ai.context.service import (
    parse_context_response,
)


def main():
    text = (
        "화요일과 목요일 오후 2시에 복지관에 가고 "
        "보통 오후 6시 전에 귀가해요."
    )

    result = parse_context_response(text)

    print("=== API Context Parse 결과 ===")
    print(
        result.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()