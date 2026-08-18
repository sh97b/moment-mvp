import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import KakaoMap from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { searchKakaoLocations } from '../../utils/kakaoLocationSearch.js'

export default function GuardianSetupBasicPage() {
  const navigate = useNavigate()
  const { setup, updateField } = useGuardianSetup()
  const [suggestions, setSuggestions] = useState([])
  const [searchStatus, setSearchStatus] = useState('idle')
  const [searchMessage, setSearchMessage] = useState('')
  const [locationEdited, setLocationEdited] = useState(false)
  const requestIdRef = useRef(0)
  const appKey = import.meta.env.VITE_KAKAO_MAP_KEY?.trim()

  const runLocationSearch = useCallback(async (rawQuery) => {
    const query = rawQuery.trim()
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId

    if (query.length < 2) {
      setSuggestions([])
      setSearchStatus('idle')
      setSearchMessage(query ? '2글자 이상 입력해 주세요.' : '')
      return
    }

    if (!appKey) {
      setSuggestions([])
      setSearchStatus('error')
      setSearchMessage('카카오맵 API 키를 확인해 주세요.')
      return
    }

    setSearchStatus('loading')
    setSearchMessage('위치를 검색하는 중입니다.')

    try {
      const results = await searchKakaoLocations(appKey, query)
      if (requestId !== requestIdRef.current) return

      setSuggestions(results)
      setSearchStatus(results.length > 0 ? 'ready' : 'empty')
      setSearchMessage(results.length > 0 ? '' : '검색 결과가 없습니다. 도로명이나 장소명을 확인해 주세요.')
    } catch {
      if (requestId !== requestIdRef.current) return
      setSuggestions([])
      setSearchStatus('error')
      setSearchMessage('위치 검색을 사용할 수 없습니다. API 키와 도메인을 확인해 주세요.')
    }
  }, [appKey])

  useEffect(() => {
    if (!locationEdited) return undefined

    const timer = window.setTimeout(() => runLocationSearch(setup.homeLocation), 350)
    return () => window.clearTimeout(timer)
  }, [locationEdited, runLocationSearch, setup.homeLocation])

  const selectLocation = (location) => {
    requestIdRef.current += 1
    updateField('homeLocation', location.address || location.name)
    updateField('homePosition', { lat: location.lat, lng: location.lng })
    setSuggestions([])
    setSearchStatus('selected')
    setSearchMessage(`‘${location.name}’ 위치를 집 위치로 선택했습니다.`)
    setLocationEdited(false)
  }

  const searchCurrentLocation = () => {
    setLocationEdited(false)
    runLocationSearch(setup.homeLocation)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!setup.homePosition) {
      setSearchStatus('error')
      setSearchMessage('검색 결과에서 집 위치를 하나 선택해 주세요.')
      return
    }
    navigate('/setup/2')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={1} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <aside className="setup-info-box">
            <strong>보호 대상자 기본 정보</strong>
            <p>집 위치는 이후 이동 거리와 귀가 방향을 판단하는 합성 기준으로 사용됩니다.</p>
          </aside>

          <label className="setup-field">
            <span>보호 대상자 이름</span>
            <input
              value={setup.personName}
              onChange={(event) => updateField('personName', event.target.value)}
              placeholder="보호 대상자 이름을 입력해 주세요"
              required
            />
          </label>

          <div className="setup-field">
            <label htmlFor="home-location">집 위치</label>
            <div className="location-input-row">
              <input
                id="home-location"
                value={setup.homeLocation}
                onChange={(event) => {
                  requestIdRef.current += 1
                  updateField('homeLocation', event.target.value)
                  updateField('homePosition', null)
                  setLocationEdited(true)
                }}
                onKeyDown={(event) => {
                  if (event.key === 'Escape') setSuggestions([])
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    searchCurrentLocation()
                  }
                }}
                placeholder="도로명, 지번 또는 장소명"
                role="combobox"
                aria-autocomplete="list"
                aria-expanded={suggestions.length > 0}
                aria-controls="home-location-suggestions"
                required
              />
              <button
                type="button"
                onClick={searchCurrentLocation}
                disabled={searchStatus === 'loading'}
              >
                {searchStatus === 'loading' ? '검색 중' : '위치 검색'}
              </button>
            </div>

            {suggestions.length > 0 && (
              <ul
                id="home-location-suggestions"
                className="location-suggestions"
                role="listbox"
                aria-label="집 위치 검색 결과"
              >
                {suggestions.map((location) => (
                  <li key={location.id} role="option" aria-selected="false">
                    <button type="button" onClick={() => selectLocation(location)}>
                      <strong>{location.name}</strong>
                      <span>{location.address}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {searchMessage && (
              <p className={`location-search-message location-search-${searchStatus}`} role="status">
                {searchMessage}
              </p>
            )}

            <div className="setup-map">
              <KakaoMap
                currentPosition={setup.homePosition}
                currentMarkerTitle=""
                ariaLabel="검색해 선택한 집 위치를 표시한 카카오 지도"
              />
            </div>
          </div>
        </div>

        <button className="setup-primary-action" type="submit">다음 단계</button>
      </form>
    </main>
  )
}
