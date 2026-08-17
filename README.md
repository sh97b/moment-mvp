# MOMENT

인지저하 고령자의 평소 이동 패턴과 다른 징후를 조기에 발견하고, 고령자 안내 후 상태를 다시 평가해 보호자 개입 여부를 결정하는 해커톤 MVP입니다.

> 본 프로젝트는 의료 진단이나 실종 판정을 제공하지 않습니다. 모든 시연 데이터는 합성 데이터이며 실제 이름, 주소, 전화번호, 생활패턴을 사용하지 않습니다.

## MVP 흐름

1. 보호자가 생활패턴을 자연어로 입력합니다.
2. FastAPI가 Gemini API를 통해 입력을 구조화합니다.
3. 저장된 합성 GPS 시나리오를 웹에서 재생합니다.
4. Feature Engineering과 Isolation Forest가 이상 징후를 계산합니다.
5. Safety Loop가 `0 → 1 → 2 → 3` 위험 단계와 하향 조건을 적용합니다.
6. 고령자 화면과 보호자 화면에 서로 다른 안내를 표시합니다.

## 고정 시연 시나리오

- 정상 이동: 위험 0 유지, 불필요한 알림 없음
- 일시 이탈 후 복귀: `0 → 1 → 0`, 고령자 안내 후 보호자 알림 없이 종료
- 이상 이동 지속: `0 → 1 → 2 → 3`, 이상 근거 표시 후 보호자 개입 안내

## 기술 스택

- Frontend: React, Vite
- Backend: FastAPI, Python 3.11
- Context parsing: Gemini API (`gemini-2.5-flash-lite`)
- Anomaly detection: scikit-learn Isolation Forest
- Map: Kakao Maps JavaScript SDK
- Data: 합성 GPS CSV/JSON
- State/Storage: 메모리 및 로컬 파일

OpenAI API, 로그인, 데이터베이스, 실제 GPS, SMS·푸시, WebSocket은 MVP 범위에서 제외합니다.

## 화면 경로

- `/setup`: 보호자 생활패턴 입력 및 구조화 결과 확인
- `/guardian`: 보호자 지도, 위험 단계, 이상 근거
- `/senior`: 고령자 안내 화면

## API

- `GET /api/health`
- `POST /api/context/parse`
- `GET /api/scenarios`
- `GET /api/replay/{scenario_id}`

세부 스키마는 [`docs/api-contract.md`](docs/api-contract.md)를 기준으로 합니다. 프론트엔드는 먼저 동일한 형태의 mock JSON으로 구현하고, 백엔드는 계약을 변경하지 않고 연결합니다.

## 개발 환경

```bash
conda create -n moment python=3.11 -y
conda activate moment
```

저장소 골격이 생성된 뒤 아래 명령을 기준으로 실행 방법을 확정합니다.

```bash
# backend
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

환경변수는 `.env.example`을 복사해 로컬에서만 설정합니다. 실제 키가 든 `.env` 파일은 커밋하지 않습니다.

## 협업 원칙

- `main`은 항상 실행 가능한 상태로 유지합니다.
- 기능 브랜치는 `feat/이름-기능`, 수정 브랜치는 `fix/기능` 형식을 사용합니다.
- API 계약, 공통 컴포넌트, 폴더 구조 변경은 팀장 확인 후 진행합니다.
- 강제 push와 다른 담당자의 파일 대규모 재작성은 금지합니다.
- 상세 작업 규칙과 담당 범위는 [`AGENTS.md`](AGENTS.md)를 따릅니다.

## 팀 운영

- 50분 작업 후 10분 휴식
- 23:00 기능 동결
- 00:30까지 시연영상 1차본과 백업 확보
- 00:30–02:30 공통 수면
- 05:20 내부 제출 마감

