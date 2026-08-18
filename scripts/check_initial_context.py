from backend.app.ai.context.service import (
    build_initial_context,
)


def main():
    result = build_initial_context(
        person_name="공나영",
        home_location="서울시 강북구 수유동 123",
        frequent_places=[
            "강북구청 경로당",
            "수유근린공원",
        ],
        usual_return_time="18:00",
        routine_text=(
            "화요일과 목요일 오후 2시쯤 복지관에 방문하고, "
            "평일에는 오전 산책을 자주 합니다."
        ),
    )

    print("=== Initial Context 생성 결과 ===")

    print(
        result.model_dump_json(
            indent=2,
        )
    )


if __name__ == "__main__":
    main()