import { useState } from 'react'
import KakaoMap from '../../components/KakaoMap.jsx'
import {
  MASTER_CONNECTION_CODE,
  readSeniorLinkCookie,
} from '../../utils/seniorLinkCookie.js'

const seniorStages = [
  {
    level: 0,
    label: '0단계 정상',
    badge: '정상',
  },
  {
    level: 1,
    label: '1단계 관심',
    badge: '관심',
    title: <>평소 산책 경로에서<br />조금 벗어났어요.</>,
    message: <>집으로 돌아가는 길을<br />안내해드릴까요?</>,
  },
  {
    level: 2,
    label: '2단계 경고',
    badge: '경고',
    title: <>평소보다 멀리<br />이동하셨어요.</>,
    message: <>집으로 돌아가는 길을<br />안내해드릴게요.</>,
  },
  {
    level: 3,
    label: '3단계 위험',
    badge: '위험',
    title: <>평소와 다른 이동이<br />계속되고 있어요.</>,
    message: <>안전한 곳에서 잠시 멈추고<br />집으로 돌아가 볼까요?</>,
  },
]

const demoHomeRoute = [
  { lat: 37.5665, lng: 126.978 },
  { lat: 37.5667, lng: 126.9783 },
  { lat: 37.567, lng: 126.9786 },
  { lat: 37.5672, lng: 126.979 },
  { lat: 37.5674, lng: 126.9794 },
]

export default function SeniorPage() {
  const [accessCode, setAccessCode] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [connectedName, setConnectedName] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [riskLevel, setRiskLevel] = useState(0)
  const [isGuidingHome, setIsGuidingHome] = useState(false)

  const handleSubmit = (event) => {
    event.preventDefault()
    const normalizedCode = accessCode.trim()

    if (!normalizedCode) {
      setErrorMessage('연결 코드를 입력해 주세요.')
      return
    }

    if (normalizedCode.length !== 5) {
      setErrorMessage('연결 코드는 5자리로 입력해 주세요.')
      return
    }

    const savedLink = readSeniorLinkCookie()
    if (normalizedCode === MASTER_CONNECTION_CODE) {
      setErrorMessage('')
      setConnectedName(savedLink?.personName ?? '보호 대상자')
      setIsConnected(true)
      return
    }

    if (!savedLink) {
      setErrorMessage('저장된 연결 정보가 없습니다. 보호자 초기 설정을 먼저 완료해 주세요.')
      return
    }

    if (normalizedCode.toUpperCase() !== savedLink.code) {
      setErrorMessage('연결 코드를 다시 확인해 주세요.')
      return
    }

    setErrorMessage('')
    setConnectedName(savedLink.personName)
    setIsConnected(true)
  }

  if (!isConnected) {
    return (
      <main className="senior-status-page">
        <header className="senior-status-header">
          <div className="senior-status-brand" aria-label="MOMENT">
            <span>M</span>
            MOMENT
          </div>
        </header>

        <section className="senior-status-content">
          <form className="senior-code-card" onSubmit={handleSubmit} noValidate>
            <h1>연결 코드 입력</h1>
            <label htmlFor="senior-access-code">보호자에게 받은 코드</label>
            <input
              id="senior-access-code"
              value={accessCode}
              onChange={(event) => {
                setAccessCode(event.target.value)
                if (errorMessage) setErrorMessage('')
              }}
              type="text"
              autoComplete="one-time-code"
              autoCapitalize="characters"
              maxLength={5}
              placeholder="5자리 코드 입력"
              aria-invalid={Boolean(errorMessage)}
              aria-describedby={errorMessage ? 'senior-code-error' : undefined}
              autoFocus
            />
            {errorMessage && (
              <p id="senior-code-error" role="alert">{errorMessage}</p>
            )}
            <button type="submit" disabled={!accessCode.trim()}>
              연결하기
            </button>
          </form>
        </section>
      </main>
    )
  }

  const stage = seniorStages[riskLevel] ?? seniorStages[0]

  const selectRiskLevel = (level) => {
    setRiskLevel(level)
    setIsGuidingHome(false)
  }

  if (isGuidingHome) {
    return (
      <main className="senior-status-page senior-connected senior-guidance-page">
        <header className="senior-status-header">
          <div className="senior-status-brand" aria-label="MOMENT">
            <span>M</span>
            MOMENT
          </div>
        </header>

        <section className="senior-guidance-content" aria-labelledby="guidance-title">
          <div className="senior-guidance-map">
            <KakaoMap
              currentPosition={demoHomeRoute.at(-1)}
              path={demoHomeRoute}
            />
          </div>
          <div className="senior-guidance-heading">
            <h1 id="guidance-title">집으로 안내합니다</h1>
            <p>직진 후 좌회전</p>
          </div>
          <div className="senior-home-summary">
            <span aria-hidden="true">🏠</span>
            <div>
              <strong>집까지 약 840m</strong>
              <p>도보 약 12분</p>
            </div>
          </div>
          <button
            className="senior-guidance-end"
            type="button"
            onClick={() => {
              setIsGuidingHome(false)
              setRiskLevel(0)
            }}
          >
            안내 종료
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className={`senior-status-page senior-connected risk-level-${riskLevel}`}>
      <header className="senior-status-header">
        <div className="senior-status-brand" aria-label="MOMENT">
          <span>M</span>
          MOMENT
        </div>
        <div className="senior-risk-badge">
          <span aria-hidden="true" />
          {stage.badge}
        </div>
      </header>

      <section className="senior-alert-content" aria-labelledby="senior-alert-title">
        {riskLevel === 0 ? (
          <div className="senior-normal-state">
            <div className="senior-normal-icon" aria-hidden="true">✓</div>
            <p>보호 대상자</p>
            <h1 id="senior-alert-title">{connectedName}</h1>
            <div className="senior-live-state" role="status" aria-live="polite">
              <span aria-hidden="true" />
              <strong>실시간 분석 중</strong>
            </div>
          </div>
        ) : (
          <div className="senior-alert-state">
            <div className="senior-alert-icon" aria-hidden="true">!</div>
            <h1 id="senior-alert-title">{stage.title}</h1>
            <p>{stage.message}</p>
            <div className="senior-alert-actions">
              <button type="button" onClick={() => setIsGuidingHome(true)}>
                집으로 안내
              </button>
              <button type="button" onClick={() => selectRiskLevel(0)}>
                괜찮아요
              </button>
            </div>
          </div>
        )}

        <div className="senior-stage-tabs" role="group" aria-label="데모 위험 단계 선택">
          {seniorStages.map((stageOption) => (
            <button
              key={stageOption.level}
              className={riskLevel === stageOption.level ? 'active' : undefined}
              type="button"
              aria-pressed={riskLevel === stageOption.level}
              onClick={() => selectRiskLevel(stageOption.level)}
            >
              {stageOption.label}
            </button>
          ))}
        </div>
      </section>
    </main>
  )
}
