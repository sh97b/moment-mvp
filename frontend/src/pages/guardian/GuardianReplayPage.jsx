import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ApiError, getHealth, getReplay, getScenarios } from '../../api/momentApi.js'
import GuardianPage from './GuardianPage.jsx'

const DEFAULT_SCENARIO_ID = 'normal'

function replayErrorMessage(error) {
  if (!(error instanceof ApiError)) return '재생 데이터를 불러오지 못했습니다.'

  if (error.status === 404) return '요청한 시나리오를 찾을 수 없습니다.'
  if (error.status === 422) return '시나리오 데이터 형식을 확인해 주세요.'
  if (error.status === 503) return '시나리오 데이터 파일을 현재 사용할 수 없습니다.'
  if (error.status === null) return '백엔드에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.'
  return error.detail || error.message
}

function ReplayStateScreen({ title, message, onRetry }) {
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

export default function GuardianReplayPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const scenarioId = searchParams.get('scenario') || DEFAULT_SCENARIO_ID
  const [health, setHealth] = useState({ status: 'loading', source: null })
  const [scenarios, setScenarios] = useState([])
  const [scenarioError, setScenarioError] = useState(null)
  const [replay, setReplay] = useState(null)
  const [replaySource, setReplaySource] = useState(null)
  const [replayStatus, setReplayStatus] = useState('loading')
  const [replayError, setReplayError] = useState(null)
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    getHealth(controller.signal)
      .then(({ data, source }) => {
        setHealth({ status: data.status === 'ok' ? 'ready' : 'error', source })
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setHealth({ status: 'error', source: null })
      })

    return () => controller.abort()
  }, [reloadKey])

  useEffect(() => {
    const controller = new AbortController()
    setScenarioError(null)

    getScenarios(controller.signal)
      .then(({ data }) => setScenarios(Array.isArray(data.scenarios) ? data.scenarios : []))
      .catch((error) => {
        if (error.name !== 'AbortError') setScenarioError(error)
      })

    return () => controller.abort()
  }, [reloadKey])

  useEffect(() => {
    const controller = new AbortController()
    setReplay(null)
    setReplaySource(null)
    setReplayStatus('loading')
    setReplayError(null)
    setCurrentFrameIndex(0)
    setIsPlaying(false)

    getReplay(scenarioId, controller.signal)
      .then(({ data, source }) => {
        if (!Array.isArray(data.frames) || data.frames.length === 0) {
          setReplayStatus('empty')
          return
        }

        setReplay(data)
        setReplaySource(source)
        setReplayStatus('ready')
        setIsPlaying(data.frames.length > 1)
      })
      .catch((error) => {
        if (error.name === 'AbortError') return
        setReplayError(error)
        setReplayStatus('error')
      })

    return () => controller.abort()
  }, [scenarioId, reloadKey])

  useEffect(() => {
    if (!replay || !isPlaying) return undefined

    if (currentFrameIndex >= replay.frames.length - 1) {
      setIsPlaying(false)
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

  const currentFrame = replay?.frames[currentFrameIndex] ?? null
  const playedFrames = useMemo(
    () => replay?.frames.slice(0, currentFrameIndex + 1) ?? [],
    [currentFrameIndex, replay],
  )

  const selectScenario = (nextScenarioId) => {
    setSearchParams({ scenario: nextScenarioId })
  }

  const restartReplay = () => {
    if (!replay) return
    setCurrentFrameIndex(0)
    setIsPlaying(replay.frames.length > 1)
  }

  if (replayStatus === 'loading') {
    return <ReplayStateScreen title="이동 데이터를 준비하고 있어요" message="잠시만 기다려 주세요." />
  }

  if (replayStatus === 'empty') {
    return (
      <ReplayStateScreen
        title="재생할 이동 데이터가 없어요"
        message="선택한 시나리오의 frame 배열이 비어 있습니다."
        onRetry={() => setReloadKey((key) => key + 1)}
      />
    )
  }

  if (replayStatus === 'error') {
    const retry = replayError instanceof ApiError && replayError.status === 404
      ? () => setSearchParams({ scenario: DEFAULT_SCENARIO_ID })
      : () => setReloadKey((key) => key + 1)

    return (
      <ReplayStateScreen
        title="이동 데이터를 불러오지 못했어요"
        message={replayErrorMessage(replayError)}
        onRetry={retry}
      />
    )
  }

  if (replay?.scenario_id !== scenarioId) {
    return <ReplayStateScreen title="이동 데이터를 준비하고 있어요" message="잠시만 기다려 주세요." />
  }

  return (
    <GuardianPage
      riskLevel={currentFrame.risk_level}
      reasons={currentFrame.reasons}
      frame={currentFrame}
      firstFrame={replay.frames[0]}
      playedFrames={playedFrames}
      currentFrameIndex={currentFrameIndex}
      totalFrames={replay.frames.length}
      isPlaying={isPlaying}
      replaySource={replaySource}
      health={health}
      scenarios={scenarios}
      scenarioError={scenarioError}
      selectedScenarioId={scenarioId}
      onSelectScenario={selectScenario}
      onTogglePlayback={() => setIsPlaying((playing) => !playing)}
      onRestart={restartReplay}
      onRetry={() => setReloadKey((key) => key + 1)}
    />
  )
}
