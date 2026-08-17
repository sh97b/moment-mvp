# MOMENT Repository Instructions

이 파일은 저장소 루트부터 하위 디렉터리 전체에 적용되는 공통 작업 지침입니다.

## Product goal

보호자 생활패턴 입력부터 합성 GPS 재생, 이상 징후 탐지, 고령자 안내, 재평가, 보호자 개입까지 하나의 반응형 웹앱에서 끝까지 시연 가능하게 만듭니다.

의료 진단, 실종 확정, 실제 위치 추적을 암시하지 말고 `평소와 다른 이동 징후`라는 표현을 사용합니다.

## Fixed scope

- Pages: `/setup`, `/guardian`, `/senior`
- Scenarios: 정상 이동, 일시 이탈 후 복귀, 이상 이동 지속
- Frontend: React + Vite
- Backend: FastAPI + Python 3.11
- AI: Gemini API for context parsing only
- ML: local Isolation Forest and explicit Safety Loop rules
- Map: Kakao Maps JavaScript SDK
- Data: synthetic GPS/context data only

Do not add authentication, a database, live mobile GPS, SMS/push delivery, WebSocket, multiple apps, or OpenAI API integration during the MVP.

## Ownership boundaries

- 반서현: `backend/app/main.py`, `backend/app/safety_loop.py`, API schema integration, final merge and submission
- 공나영: Gemini context parser, Isolation Forest model, model tests and fallback behavior
- 오현동: shared React shell, Kakao Map, guardian dashboard, frontend API client
- 정아영: synthetic GPS data, feature engineering, replay frames, comparison evaluation
- 손상혁: setup/senior UI, design system, QA, presentation and demo video

Do not reorganize or broadly rewrite another owner's files without coordinating first. When a shared file must change, keep the patch minimal and report the exact contract impact.

## API contract

`docs/api-contract.md` is the source of truth. Do not rename, remove, or change the type of response fields without team lead approval.

Every replay frame must include:

`timestamp`, `lat`, `lng`, `features`, `anomaly_score`, `risk_level`, `reasons`, `elderly_alert`, `guardian_alert`

Return the full replay frame array in one response. The frontend simulates real time with a timer; do not introduce WebSocket for the MVP.

## Data and secrets

- Never commit `.env`, API keys, real names, addresses, phone numbers, or real movement histories.
- Commit only variable names and safe defaults to `.env.example`.
- Send only synthetic data to Gemini free tier.
- Keep a deterministic local fallback JSON for Gemini failures and quota errors.
- Use fixed seeds when generating evaluation data so results are reproducible.

## Implementation rules

- Prefer the smallest change that completes the assigned scenario.
- Keep feature names and units consistent across CSV, model, API, and UI.
- Isolation Forest raw scores must be converted consistently; test the sign and threshold explicitly.
- Keep risk reasons human-readable and derived from actual frame features.
- Do not add a production dependency without updating `package-lock.json` or `requirements.txt` in the same commit.
- Do not change shared mock JSON independently from `docs/api-contract.md`.
- Do not use force push on shared branches.

## Verification

Run the checks relevant to the files changed. If the command is not available yet, state that clearly instead of claiming success.

```bash
# backend
pytest backend/tests

# frontend
cd frontend
npm run lint
npm run build
```

Before merge, manually verify all three demo scenarios and confirm that no secret or personal data is present in the diff.

## Completion report

When finishing a task, report:

1. Files changed
2. Behavior implemented
3. Tests or manual checks run
4. Remaining limitation or handoff note

