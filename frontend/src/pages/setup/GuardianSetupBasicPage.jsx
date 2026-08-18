import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import KakaoMap, { loadKakaoMapsSdk } from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'

const MAX_SUGGESTIONS = 6

function toLocationResult(result, type) {
  const lat = Number(result.y)
  const lng = Number(result.x)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null

  const address = result.road_address_name
    || result.road_address?.address_name
    || result.address_name

  return {
    id: `${type}:${lat}:${lng}`,
    name: type === 'place' ? result.place_name : address,
    address,
    lat,
    lng,
    type,
  }
}

function searchKakaoLocations(query) {
  return new Promise((resolve, reject) => {
    const services = window.kakao?.maps?.services
    if (!services) {
      reject(new Error('카카오맵 검색 라이브러리를 불러오지 못했습니다.'))
      return
    }

    const places = new services.Places()
    const geocoder = new services.Geocoder()
    const searchResults = { addresses: [], places: [] }
    let completedCount = 0

    const complete = () => {
      completedCount += 1
      if (completedCount < 2) return

      const seen = new Set()
      const results = [...searchResults.addresses, ...searchResults.places]
        .map(({ result, type }) => toLocationResult(result, type))
        .filter((location) => {
          if (!location) return false
          const key = `${location.lat.toFixed(6)}:${location.lng.toFixed(6)}`
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
        .slice(0, MAX_SUGGESTIONS)

      resolve(results)
    }

    geocoder.addressSearch(query, (results, status) => {
      if (status === services.Status.OK) {
        searchResults.addresses = results.map((result) => ({ result, type: 'address' }))
      }
      complete()
    }, { size: 3 })

    places.keywordSearch(query, (results, status) => {
      if (status === services.Status.OK) {
        searchResults.places = results.map((result) => ({ result, type: 'place' }))
      }
      complete()
    }, { size: MAX_SUGGESTIONS })
  })
}

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
      await loadKakaoMapsSdk(appKey)
      const results = await searchKakaoLocations(query)
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
            <span>보호 대상자 표시 이름</span>
            <input
              value={setup.personName}
              onChange={(event) => updateField('personName', event.target.value)}
              placeholder="합성 표시 이름을 입력해 주세요"
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
