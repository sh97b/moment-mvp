import { mockHealth, mockReplays, mockScenarios } from '../mocks/replayData.js'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const mockMode = import.meta.env.VITE_USE_MOCK_API ?? 'auto'
const forceMock = mockMode === 'true'
const allowMockFallback = mockMode !== 'false'

export class ApiError extends Error {
  constructor(message, { status = null, detail = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function clone(value) {
  return structuredClone(value)
}

async function request(path, signal) {
  let response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, { signal })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('백엔드에 연결할 수 없습니다.')
  }

  let payload = null
  try {
    payload = await response.json()
  } catch {
    // 오류 응답에 JSON 본문이 없어도 HTTP 상태를 유지한다.
  }

  if (!response.ok) {
    throw new ApiError(`API 요청 실패: ${response.status}`, {
      status: response.status,
      detail: payload?.detail ?? null,
    })
  }

  return payload
}

function shouldUseFallback(error, fallbackExists) {
  if (!allowMockFallback || !fallbackExists) return false
  return error instanceof ApiError && (error.status === null || error.status === 404)
}

export async function getHealth(signal) {
  if (forceMock) return { data: clone(mockHealth), source: 'mock' }

  try {
    return { data: await request('/api/health', signal), source: 'api' }
  } catch (error) {
    if (!shouldUseFallback(error, true)) throw error
    return { data: clone(mockHealth), source: 'mock' }
  }
}

export async function getScenarios(signal) {
  if (forceMock) return { data: clone(mockScenarios), source: 'mock' }

  try {
    return { data: await request('/api/scenarios', signal), source: 'api' }
  } catch (error) {
    if (!shouldUseFallback(error, true)) throw error
    return { data: clone(mockScenarios), source: 'mock' }
  }
}

export async function getReplay(scenarioId, signal) {
  const fallback = mockReplays[scenarioId]
  if (forceMock && fallback) return { data: clone(fallback), source: 'mock' }

  try {
    return {
      data: await request(`/api/replay/${encodeURIComponent(scenarioId)}`, signal),
      source: 'api',
    }
  } catch (error) {
    if (!shouldUseFallback(error, Boolean(fallback))) throw error
    return { data: clone(fallback), source: 'mock' }
  }
}
