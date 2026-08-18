from backend.app.ai.risk_engine import (
    NORMAL,
    INTEREST,
    CAUTION,
    DANGER,
    determine_initial_risk,
    get_effective_abnormal_count,
)


# 이상 상태가 연속 몇 개 frame 동안 지속되면
# 다음 단계로 상승시킬지 결정
#
# 현재 데이터가 1분 간격이므로
# 3 frames = 약 3분

PERSIST_FRAMES = 3


class SafetyLoop:
    def __init__(self):
        # 현재 위험 단계
        self.current_level = NORMAL

        # 현재 단계 진입 이후
        # 이상 행동이 연속으로 지속된 시간
        self.abnormal_streak = 0

        # 직전 Feature 값
        self.previous_turn = None
        self.previous_revisit = None


    def reset_streak(self):
        self.abnormal_streak = 0


    def increase_streak(self):
        self.abnormal_streak += 1


    def update(
        self,
        prediction: dict,
    ) -> dict:
        """
        새로운 1분 단위 prediction을 받아
        Safety Loop를 한 번 수행한다.
        """

        previous_level = self.current_level

        current_turn = prediction[
            "turn_10min"
        ]

        current_revisit = prediction[
            "revisit_15min"
        ]

        abnormal_count = get_effective_abnormal_count(
        prediction
        )


        # =====================================
        # 1. 현재 Feature가 증가 중인지 확인
        # =====================================

        is_increasing = False

        if (
            self.previous_turn is not None
            and self.previous_revisit is not None
        ):
            is_increasing = (
                current_turn > self.previous_turn
                or
                current_revisit > self.previous_revisit
            )


        # =====================================
        # 2. 현재 한 시점의 초기 위험 단계
        # =====================================

        initial_level = determine_initial_risk(
            prediction
        )


        # =====================================
        # 3. 현재 상태가 NORMAL
        # =====================================

        if self.current_level == NORMAL:

            if initial_level == NORMAL:
                self.current_level = NORMAL
                self.reset_streak()

            elif initial_level == INTEREST:
                # Feature 하나 이상
                # → 관심 단계 진입
                self.current_level = INTEREST

                # 관심 단계에 이제 막 들어왔기 때문에
                # 지속시간은 0부터 시작
                self.reset_streak()

            elif initial_level == CAUTION:
                # 두 Feature가 동시에 이상이면
                # 바로 주의 단계
                self.current_level = CAUTION
                self.reset_streak()


        # =====================================
        # 4. 현재 상태가 INTEREST
        # =====================================

        elif self.current_level == INTEREST:

            if abnormal_count == 0:
                # 정상화
                self.current_level = NORMAL
                self.reset_streak()

            elif abnormal_count == 2:
                # 두 Feature 모두 이상
                # → 즉시 주의
                self.current_level = CAUTION
                self.reset_streak()

            else:
                # Feature 하나가 계속 이상
                self.increase_streak()

                # 관심 알림 이후
                # 이상 행동이 일정 시간 지속
                if (
                    self.abnormal_streak
                    >= PERSIST_FRAMES
                ):
                    self.current_level = CAUTION
                    self.reset_streak()


        # =====================================
        # 5. 현재 상태가 CAUTION
        # =====================================

        elif self.current_level == CAUTION:

            if abnormal_count == 0:
                # 이상이 사라졌으면
                # 한 단계 하향
                self.current_level = INTEREST
                self.reset_streak()

            else:
                # 하나든 둘이든 이상 행동이
                # 계속 남아있으면 지속으로 판단
                self.increase_streak()

                # 주의 알림 이후에도
                # 이상 행동이 계속 지속되면 위험
                if (
                    self.abnormal_streak
                    >= PERSIST_FRAMES
                ):
                    self.current_level = DANGER
                    self.reset_streak()


        # =====================================
        # 6. 현재 상태가 DANGER
        # =====================================

        elif self.current_level == DANGER:

            if abnormal_count == 0:
                # 정상화되기 시작하면
                # 바로 정상으로 보내지 않고
                # 한 단계 하향
                self.current_level = CAUTION
                self.reset_streak()

            else:
                # 아직 이상이면 위험 유지
                self.current_level = DANGER


        # =====================================
        # 7. 현재 값을 다음 비교용으로 저장
        # =====================================

        self.previous_turn = current_turn
        self.previous_revisit = current_revisit


        # =====================================
        # 8. 결과 반환
        # =====================================

        return {
            "previous_level": previous_level,
            "current_level": self.current_level,

            "level_changed":
                previous_level != self.current_level,

            "abnormal_streak":
                self.abnormal_streak,

            "abnormal_feature_count":
                abnormal_count,

            "is_increasing":
                is_increasing,

            "turn_abnormal":
                prediction["turn_abnormal"],

            "revisit_abnormal":
                prediction["revisit_abnormal"],

            "anomaly_score":
                prediction["anomaly_score"],
        }