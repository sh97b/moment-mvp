import { useEffect, useState } from 'react'
import KakaoMap from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { readActiveGuardianProfile } from '../../utils/guardianProfile.js'

const riskStages = {
  0: {
    label: '0단계 정상',
    summary: '평소 범위 내',
    title: '✓ 정상 이동 중',
    message: '현재 위치는 평소 이동패턴 범위에 있습니다. MOMENT가 계속 분석합니다.',
  },
  1: {
    label: '1단계 주의',
    summary: '이동 징후 확인 중',
    title: '평소와 다른 이동 징후 확인 중',
    message: '한 번의 기준 초과 또는 평소와 다른 이동 징후가 확인되었습니다.',
  },
  2: {
    label: '2단계 경고',
    summary: '이동 징후 지속',
    title: '평소와 다른 이동 징후가 이어지고 있습니다',
    message: '여러 이동 징후가 연속적으로 위치에서 확인되어 보호자 화면에 안내합니다.',
  },
  3: {
    label: '3단계 위험',
    summary: '보호자 확인 필요',
    title: '보호자 확인이 필요합니다',
    message: '고령자 안내 후에도 평소와 다른 이동 징후와 집과의 거리 증가가 이어지고 있습니다.',
  },
}

function formatClock(timestamp) {
  return new Intl.DateTimeFormat('ko-KR', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(timestamp))
}

function formatRelativeTime(timestamp, currentTimestamp) {
  const elapsedMs = Math.max(0, new Date(currentTimestamp) - new Date(timestamp))
  const elapsedMinutes = Math.floor(elapsedMs / 60000)

  if (elapsedMinutes < 1) return '방금 전'
  if (elapsedMinutes < 60) return `${elapsedMinutes}분 전`

  const elapsedHours = Math.floor(elapsedMinutes / 60)
  if (elapsedHours < 24) return `${elapsedHours}시간 전`

  return `${Math.floor(elapsedHours / 24)}일 전`
}

function formatElapsed(firstTimestamp, currentTimestamp) {
  const elapsedMs = Math.max(0, new Date(currentTimestamp) - new Date(firstTimestamp))
  const totalMinutes = Math.floor(elapsedMs / 60000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  if (hours === 0) return `${minutes}분`
  return `${hours}시간 ${minutes}분`
}

function formatDistance(distance) {
  if (!Number.isFinite(distance)) return '데이터 없음'
  if (distance >= 1000) return `${(distance / 1000).toFixed(1)}km`
  return `${Math.round(distance)}m`
}

function formatDistanceDelta(delta) {
  if (!Number.isFinite(delta)) return '변화 데이터 없음'
  if (delta === 0) return '직전 위치 기록과 동일'
  return `직전 위치 기록보다 ${Math.abs(Math.round(delta))}m ${delta > 0 ? '증가' : '감소'}`
}

function collectAlertLogs(frames) {
  const alertLogs = []
  const activeAlertKeys = new Map()

  frames.forEach((replayFrame, frameIndex) => {
    const alerts = [
      { source: 'elderly', value: replayFrame.elderly_alert },
      { source: 'guardian', value: replayFrame.guardian_alert },
    ]

    alerts.forEach(({ source, value }) => {
      if (!value?.title || !value?.message) {
        activeAlertKeys.delete(source)
        return
      }

      const alertKey = `${value.title}:${value.message}`
      if (activeAlertKeys.get(source) === alertKey) return

      alertLogs.push({
        id: `movement:${source}:${replayFrame.timestamp}:${frameIndex}`,
        kind: 'movement',
        label: '이동 알림',
        title: value.title,
        message: value.message,
        timestamp: replayFrame.timestamp,
        riskLevel: replayFrame.risk_level,
      })
      activeAlertKeys.set(source, alertKey)
    })
  })

  return alertLogs.sort(
    (first, second) => new Date(first.timestamp) - new Date(second.timestamp),
  )
}

export default function GuardianPage({
  riskLevel,
  reasons,
  frame,
  firstFrame,
  playedFrames,
  currentFrameIndex,
  totalFrames,
  isPlaying,
  replaySource,
  health,
  scenarios,
  scenarioError,
  selectedScenarioId,
  onSelectScenario,
  onTogglePlayback,
  onRestart,
  onRetry,
}) {
  const [manualNormalLog, setManualNormalLog] = useState(null)
  const [normalOutingFeedback, setNormalOutingFeedback] = useState(false)
  const effectiveRiskLevel = manualNormalLog ? 0 : riskLevel
  const stage = riskStages[effectiveRiskLevel] ?? riskStages[0]
  const { setup } = useGuardianSetup()
  const activeProfile = readActiveGuardianProfile()
  const personName = activeProfile?.name || setup.personName.trim() || '보호 대상자'
  const guardianCode = activeProfile?.code || '코드 없음'
  const path = playedFrames.map(({ lat, lng }) => ({ lat, lng }))
  const currentPosition = { lat: frame.lat, lng: frame.lng }
  const replayFinished = currentFrameIndex === totalFrames - 1
  const alertLogs = [
    ...collectAlertLogs(playedFrames),
    ...(manualNormalLog ? [manualNormalLog] : []),
  ].sort((first, second) => new Date(first.timestamp) - new Date(second.timestamp))
  const frameAlerts = [frame.elderly_alert, frame.guardian_alert].filter(
    (alert) => alert?.title && alert?.message,
  )
  const frameAlert = frameAlerts[frameAlerts.length - 1] ?? null
  const currentStatus = manualNormalLog
    ? {
        kind: 'normal',
        label: '보호자 확인',
        title: '정상 외출로 확인했습니다',
        message: '보호자 확인으로 위험 단계를 0단계 정상으로 변경했습니다.',
      }
    : frameAlert
      ? { ...frameAlert, kind: 'movement', label: '이동 알림' }
      : {
          kind: 'normal',
          label: '현재 상태',
          title: effectiveRiskLevel === 0 ? '✓ 정상 이동 중입니다' : stage.title,
          message: effectiveRiskLevel === 0
            ? '현재 확인된 평소와 다른 이동 징후가 없습니다.'
            : stage.message,
        }
  const currentStatusTimestamp = manualNormalLog?.timestamp ?? frame.timestamp

  useEffect(() => {
    if (!normalOutingFeedback) return undefined

    const timer = window.setTimeout(() => setNormalOutingFeedback(false), 2600)
    return () => window.clearTimeout(timer)
  }, [normalOutingFeedback])

  const confirmNormalOuting = () => {
    setManualNormalLog({
      id: `manual-normal:${frame.timestamp}`,
      kind: 'manual',
      label: '보호자 확인',
      title: '정상 외출로 처리',
      message: '보호자가 현재 이동을 정상 외출로 확인해 위험 단계를 0단계로 변경했습니다.',
      timestamp: frame.timestamp,
      riskLevel,
    })
    setNormalOutingFeedback(true)
  }

  return (
    <main className={`guardian-page risk-level-${effectiveRiskLevel}`}>
      <header className="guardian-hero">
        <div className="guardian-code-row">
          <span>등록 코드</span>
          <strong>{guardianCode}</strong>
        </div>

        <div className="guardian-brand-row">
          <div className="guardian-brand" aria-label="MOMENT">
            <span className="guardian-brand-mark">M</span>
            <span>MOMENT</span>
          </div>
          <div className="live-badge">
            <span className="status-dot" />
            실시간 분석중
          </div>
        </div>

        <div className="guardian-person-row">
          <div>
            <p className="guardian-label">보호 대상자</p>
            <h1>{personName}</h1>
          </div>
          <div className="risk-badge">
            <span className="status-dot" />
            {stage.label}
          </div>
        </div>

      </header>

      <div className="guardian-content">
        <section className="scenario-panel" aria-labelledby="scenario-title">
          <div className="scenario-panel-heading">
            <div>
              <span>데모 시나리오</span>
              <h2 id="scenario-title">이동 재생 선택</h2>
            </div>
            <span className={`api-health api-health-${health.status}`}>
              {health.status === 'ready'
                ? health.source === 'mock' ? 'Mock 사용' : 'API 연결'
                : health.status === 'loading' ? '확인 중' : '연결 확인'}
            </span>
          </div>

          {scenarioError ? (
            <div className="scenario-inline-error">
              시나리오 목록을 불러오지 못했습니다.
              <button type="button" onClick={onRetry}>다시 시도</button>
            </div>
          ) : (
            <div className="scenario-tabs">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  className={scenario.id === selectedScenarioId ? 'active' : undefined}
                  type="button"
                  onClick={() => {
                    setManualNormalLog(null)
                    setNormalOutingFeedback(false)
                    onSelectScenario(scenario.id)
                  }}
                  title={scenario.description}
                >
                  {scenario.name}
                </button>
              ))}
            </div>
          )}

          <div className="replay-controls">
            <div>
              <strong>{currentFrameIndex + 1} / {totalFrames}</strong>
              <span>{replayFinished ? '재생 완료' : isPlaying ? '자동 재생 중' : '일시 정지'}</span>
            </div>
            <div>
              <button
                type="button"
                onClick={() => {
                  setManualNormalLog(null)
                  setNormalOutingFeedback(false)
                  onRestart()
                }}
              >
                처음부터
              </button>
              <button type="button" onClick={onTogglePlayback} disabled={replayFinished}>
                {isPlaying ? '일시 정지' : '재생'}
              </button>
            </div>
          </div>
        </section>

        <section
          className={`status-alert-card status-alert-${currentStatus.kind}`}
          aria-live="polite"
        >
          <div className="status-alert-meta">
            <div className="status-alert-label">
              <span>{currentStatus.label}</span>
            </div>
            <time dateTime={currentStatusTimestamp}>{formatClock(currentStatusTimestamp)}</time>
          </div>
          <div className="status-alert-title-row">
            <h2>{currentStatus.title}</h2>
            {riskLevel >= 2 && replayFinished && !manualNormalLog && (
                <button
                  className="normal-outing-button"
                  type="button"
                  onClick={confirmNormalOuting}
                >
                  정상 외출
                </button>
            )}
          </div>
          <p>{currentStatus.message}</p>

          {alertLogs.length > 0 && (
            <details className="alert-history-details">
              <summary className="alert-history-toggle">
                <span>알림 기록 {alertLogs.length}건</span>
                <strong>펼쳐보기</strong>
              </summary>

              <ol className="alert-history-list">
                {[...alertLogs].reverse().map((alert) => (
                  <li
                    key={alert.id}
                    className={`alert-history-item alert-history-${alert.kind}${
                      alert.kind === 'movement' ? ` alert-history-risk-${alert.riskLevel}` : ''
                    }`}
                  >
                    <div>
                      <span>{alert.label}</span>
                      <time dateTime={alert.timestamp}>
                        {formatClock(alert.timestamp)} · {formatRelativeTime(alert.timestamp, frame.timestamp)}
                      </time>
                    </div>
                    <strong>{alert.title}</strong>
                    <p>{alert.message}</p>
                  </li>
                ))}
              </ol>
            </details>
          )}
        </section>

        <section className="dashboard-card map-card" aria-labelledby="location-title">
          <div className="card-heading">
            <h2 id="location-title">현재 위치 및 이동 경로</h2>
            <time dateTime={frame.timestamp}>{formatClock(frame.timestamp)} 기준</time>
          </div>
          <KakaoMap currentPosition={currentPosition} path={path} currentMarkerTitle="" />
        </section>

        <section className="summary-grid" aria-label="현재 이동 요약">
          <article className="dashboard-card summary-card">
            <p>현재 외출 시간</p>
            <strong>{formatElapsed(firstFrame.timestamp, frame.timestamp)}</strong>
            <span>이동 시작 시각 기준</span>
          </article>
          <article className="dashboard-card summary-card">
            <p>집과의 거리</p>
            <strong>{formatDistance(frame.features?.home_distance_m)}</strong>
            <span>{formatDistanceDelta(frame.features?.home_distance_delta_m)}</span>
          </article>
        </section>

        <section
          className={`dashboard-card analysis-card${
            manualNormalLog ? ` analysis-before-confirmation analysis-risk-${manualNormalLog.riskLevel}` : ''
          }`}
          aria-labelledby="analysis-title"
        >
          <div className="analysis-heading">
            <h2 id="analysis-title">
              {manualNormalLog ? '정상 외출 처리 전 이동 분석' : '현재 이동 분석'}
            </h2>
            <strong>{Math.round(frame.anomaly_score * 100)}점</strong>
          </div>
          {manualNormalLog && (
            <p className="manual-analysis-notice">
              아래 내용은 보호자가 정상 외출로 확인하기 직전의 분석 결과입니다.
            </p>
          )}
          <div className="anomaly-meter" aria-label={`이상 점수 ${Math.round(frame.anomaly_score * 100)}점`}>
            <span style={{ width: `${Math.min(100, Math.max(0, frame.anomaly_score * 100))}%` }} />
          </div>
          {reasons.length > 0 ? (
            <ul className="reason-list">
              {reasons.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
          ) : (
            <p className="empty-reasons">현재 확인된 평소와 다른 이동 징후가 없습니다.</p>
          )}
        </section>

      </div>

      {normalOutingFeedback && (
        <div className="normal-outing-toast" role="status">
          정상 외출로 처리하고 알림 기록에 저장했습니다.
        </div>
      )}
    </main>
  )
}
