import { useEffect, useState } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { getReplay, getScenarios } from '../../api/momentApi.js'
import KakaoMap from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { readActiveGuardianProfile } from '../../utils/guardianProfile.js'

const DEFAULT_SCENARIO_ID = 'normal'
const DEMO_SCENARIO_IDS = new Set(['normal', 'temporary_return', 'persistent_anomaly'])

const riskStages = {
  0: {
    label: '0단계 정상',
    title: '✓ 정상 이동 중입니다',
    message: '현재 위치는 평소 이동 패턴 범위에 있습니다.',
  },
  1: {
    label: '1단계 주의',
    title: '평소와 다른 이동 징후를 확인 중입니다',
    message: '잠시 멈추고 익숙한 길인지 확인해 주세요.',
  },
  2: {
    label: '2단계 경고',
    title: '평소와 다른 이동 징후가 이어지고 있습니다',
    message: '안전한 곳에서 주변을 확인하고 익숙한 길로 이동해 주세요.',
  },
  3: {
    label: '3단계 위험',
    title: '보호자가 현재 이동 상태를 확인하고 있습니다',
    message: '안전한 곳에 머물며 잠시 기다려 주세요.',
  },
}

function formatClock(timestamp) {
  return new Intl.DateTimeFormat('ko-KR', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(new Date(timestamp))
}

function SeniorStateScreen({ title, message, onRetry }) {
  return (
    <main className="replay-state-page">
      <div className="replay-state-brand"><span>M</span>MOMENT</div>
      <section role="status">
        <h1>{title}</h1>
        <p>{message}</p>
        {onRetry && <button type="button" onClick={onRetry}>다시 시도</button>}
      </section>
    </main>
  )
}

export default function SeniorPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const scenarioId = searchParams.get('scenario') || DEFAULT_SCENARIO_ID
  const { setup } = useGuardianSetup()
  const activeProfile = readActiveGuardianProfile()
  const [scenarios, setScenarios] = useState([])
  const [replay, setReplay] = useState(null)
  const [status, setStatus] = useState('loading')
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    getScenarios(controller.signal)
      .then(({ data }) => setScenarios(
        Array.isArray(data.scenarios)
          ? data.scenarios.filter(({ id }) => DEMO_SCENARIO_IDS.has(id))
          : [],
      ))
      .catch((error) => {
        if (error.name !== 'AbortError') setScenarios([])
      })

    return () => controller.abort()
  }, [reloadKey])

  useEffect(() => {
    const controller = new AbortController()
    setReplay(null)
    setStatus('loading')
    setCurrentFrameIndex(0)
    setIsPlaying(false)

    getReplay(scenarioId, controller.signal)
      .then(({ data }) => {
        if (!Array.isArray(data.frames) || data.frames.length === 0) {
          setStatus('empty')
          return
        }

        setReplay(data)
        setStatus('ready')
        setIsPlaying(data.frames.length > 1)
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setStatus('error')
      })

    return () => controller.abort()
  }, [reloadKey, scenarioId])

  useEffect(() => {
    if (!replay || !isPlaying || currentFrameIndex >= replay.frames.length - 1) {
      return undefined
    }

    const interval = Number.isFinite(replay.interval_ms) && replay.interval_ms > 0
      ? replay.interval_ms
      : 1000
    const timer = window.setTimeout(() => {
      setCurrentFrameIndex((index) => Math.min(index + 1, replay.frames.length - 1))
    }, interval)

    return () => window.clearTimeout(timer)
  }, [currentFrameIndex, isPlaying, replay])

  if (status === 'loading') {
    return <SeniorStateScreen title="이동 정보를 준비하고 있어요" message="잠시만 기다려 주세요." />
  }

  if (status === 'empty') {
    return (
      <SeniorStateScreen
        title="표시할 위치 정보가 없어요"
        message="선택한 시나리오의 이동 데이터가 비어 있습니다."
        onRetry={() => setReloadKey((key) => key + 1)}
      />
    )
  }

  if (status === 'error') {
    return (
      <SeniorStateScreen
        title="이동 정보를 불러오지 못했어요"
        message="잠시 후 다시 시도해 주세요."
        onRetry={() => setReloadKey((key) => key + 1)}
      />
    )
  }

  if (replay?.scenario_id !== scenarioId) {
    return <SeniorStateScreen title="이동 정보를 준비하고 있어요" message="잠시만 기다려 주세요." />
  }

  const frame = replay.frames[currentFrameIndex]
  const path = replay.frames.slice(0, currentFrameIndex + 1).map(({ lat, lng }) => ({ lat, lng }))
  const stage = riskStages[frame.risk_level] ?? riskStages[0]
  const replayFinished = currentFrameIndex === replay.frames.length - 1
  const personName = `${(activeProfile?.name || setup.personName.trim() || '보호 대상자')}님`

  if (!activeProfile && !setup.personName) {
    return <Navigate to="/senior/enter" replace />
  }

  return (
    <main className={`senior-page risk-level-${frame.risk_level}`}>
      <header className="guardian-hero senior-hero">
        <div className="guardian-brand-row">
          <div className="guardian-brand" aria-label="MOMENT">
            <span className="guardian-brand-mark">M</span>
            <span>MOMENT</span>
          </div>
        </div>

        <div className="guardian-person-row senior-person-row">
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

      <div className="guardian-content senior-content">
        <section className="senior-scenario-panel" aria-label="시나리오 선택">
          <span className="senior-scenario-label">시나리오</span>
          <div className="senior-scenario-tabs">
            {scenarios.map((scenario) => (
              <button
                key={scenario.id}
                type="button"
                className={scenario.id === scenarioId ? 'active' : undefined}
                onClick={() => setSearchParams({ scenario: scenario.id })}
              >
                {scenario.name}
              </button>
            ))}
          </div>
        </section>

        <section className="dashboard-card map-card senior-map-card" aria-labelledby="senior-location-title">
          <div className="card-heading senior-card-heading">
            <h2 id="senior-location-title">현재 위치</h2>
            <time dateTime={frame.timestamp}>{formatClock(frame.timestamp)} 기준</time>
          </div>
          <KakaoMap
            currentPosition={{ lat: frame.lat, lng: frame.lng }}
            path={path}
            ariaLabel="현재 위치와 이동 경로를 함께 보여주는 카카오 지도"
            interactive={false}
          />
        </section>
      </div>
    </main>
  )
}
