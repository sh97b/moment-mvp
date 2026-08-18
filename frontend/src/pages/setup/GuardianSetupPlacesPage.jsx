import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import KakaoMap from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { searchKakaoLocations } from '../../utils/kakaoLocationSearch.js'

const MAX_PLACE_DISTANCE_KM = 5
const EARTH_RADIUS_KM = 6371

function isCoordinate(position) {
  return Number.isFinite(position?.lat) && Number.isFinite(position?.lng)
}

function toRadians(degrees) {
  return degrees * (Math.PI / 180)
}

function getDistanceKm(start, end) {
  if (!isCoordinate(start) || !isCoordinate(end)) return null

  const latitudeDelta = toRadians(end.lat - start.lat)
  const longitudeDelta = toRadians(end.lng - start.lng)
  const startLatitude = toRadians(start.lat)
  const endLatitude = toRadians(end.lat)
  const haversine = (
    Math.sin(latitudeDelta / 2) ** 2
    + Math.cos(startLatitude) * Math.cos(endLatitude) * Math.sin(longitudeDelta / 2) ** 2
  )

  return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine))
}

function formatDistance(distanceKm) {
  if (!Number.isFinite(distanceKm)) return '거리 확인 불가'
  if (distanceKm < 1) return `집에서 ${Math.round(distanceKm * 1000)}m`
  return `집에서 ${distanceKm.toFixed(1)}km`
}

export default function GuardianSetupPlacesPage() {
  const navigate = useNavigate()
  const { setup, updateField } = useGuardianSetup()
  const [activePlaceIndex, setActivePlaceIndex] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [searchStatus, setSearchStatus] = useState('idle')
  const [searchMessage, setSearchMessage] = useState('')
  const [placeEdited, setPlaceEdited] = useState(false)
  const requestIdRef = useRef(0)
  const appKey = import.meta.env.VITE_KAKAO_MAP_KEY?.trim()

  const updatePlaceLocation = (index, value) => {
    const locations = setup.placeLocations ?? setup.places.map(() => null)
    updateField('placeLocations', locations.map((location, itemIndex) => (
      itemIndex === index ? value : location
    )))
  }

  const updatePlace = (index, value) => {
    requestIdRef.current += 1
    updateField('places', setup.places.map((place, itemIndex) => (
      itemIndex === index ? value : place
    )))
    updatePlaceLocation(index, null)
    setActivePlaceIndex(index)
    setPlaceEdited(true)
  }

  const runPlaceSearch = useCallback(async (index, rawQuery) => {
    const query = rawQuery.trim()
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    setActivePlaceIndex(index)

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
    setSearchMessage('장소를 검색하는 중입니다.')

    try {
      const results = await searchKakaoLocations(appKey, query)
      if (requestId !== requestIdRef.current) return

      setSuggestions(results)
      setSearchStatus(results.length > 0 ? 'ready' : 'empty')
      setSearchMessage(results.length > 0 ? '' : '검색 결과가 없습니다. 장소명이나 주소를 확인해 주세요.')
    } catch {
      if (requestId !== requestIdRef.current) return
      setSuggestions([])
      setSearchStatus('error')
      setSearchMessage('장소 검색을 사용할 수 없습니다. API 키와 도메인을 확인해 주세요.')
    }
  }, [appKey])

  useEffect(() => {
    if (!placeEdited || activePlaceIndex === null) return undefined

    const query = setup.places[activePlaceIndex] ?? ''
    const timer = window.setTimeout(() => runPlaceSearch(activePlaceIndex, query), 350)
    return () => window.clearTimeout(timer)
  }, [activePlaceIndex, placeEdited, runPlaceSearch, setup.places])

  const selectPlace = (index, location) => {
    if (!isCoordinate(setup.homePosition)) {
      setSearchStatus('error')
      setSearchMessage('집 위치를 먼저 검색해 선택해 주세요.')
      return
    }

    const distanceKm = getDistanceKm(setup.homePosition, location)
    if (!Number.isFinite(distanceKm) || distanceKm > MAX_PLACE_DISTANCE_KM) {
      setSearchStatus('error')
      setSearchMessage(
        `${formatDistance(distanceKm)} 떨어져 있어 주요 장소로 등록할 수 없습니다. ${MAX_PLACE_DISTANCE_KM}km 이내의 데모용 장소를 선택해 주세요.`,
      )
      return
    }

    requestIdRef.current += 1
    updateField('places', setup.places.map((place, itemIndex) => (
      itemIndex === index ? location.name : place
    )))
    updatePlaceLocation(index, {
      name: location.name,
      address: location.address,
      lat: location.lat,
      lng: location.lng,
      homeDistanceKm: distanceKm,
    })
    setSuggestions([])
    setSearchStatus('selected')
    setSearchMessage(`‘${location.name}’ 장소를 주요 장소로 선택했습니다.`)
    setPlaceEdited(false)
  }

  const removePlace = (index) => {
    requestIdRef.current += 1
    updateField('places', setup.places.filter((_, itemIndex) => itemIndex !== index))
    updateField(
      'placeLocations',
      (setup.placeLocations ?? []).filter((_, itemIndex) => itemIndex !== index),
    )
    setActivePlaceIndex(null)
    setSuggestions([])
    setSearchMessage('')
    setPlaceEdited(false)
  }

  const addPlace = () => {
    updateField('places', [...setup.places, ''])
    updateField('placeLocations', [...(setup.placeLocations ?? []), null])
    setActivePlaceIndex(setup.places.length)
    setSuggestions([])
    setSearchMessage('')
    setPlaceEdited(false)
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!isCoordinate(setup.homePosition)) {
      setActivePlaceIndex(0)
      setSearchStatus('error')
      setSearchMessage('집 위치를 먼저 검색해 선택해 주세요.')
      return
    }

    const locations = setup.placeLocations ?? []
    const missingLocationIndex = setup.places.findIndex(
      (place, index) => place.trim() && !isCoordinate(locations[index]),
    )
    if (missingLocationIndex >= 0) {
      setActivePlaceIndex(missingLocationIndex)
      setSearchStatus('error')
      setSearchMessage('입력한 장소를 검색 결과에서 선택해 주세요.')
      return
    }

    const invalidLocationIndex = locations.findIndex((location) => {
      if (!isCoordinate(location)) return false
      const distanceKm = getDistanceKm(setup.homePosition, location)
      return !Number.isFinite(distanceKm) || distanceKm > MAX_PLACE_DISTANCE_KM
    })
    if (invalidLocationIndex >= 0) {
      setActivePlaceIndex(invalidLocationIndex)
      setSearchStatus('error')
      setSearchMessage(`집에서 ${MAX_PLACE_DISTANCE_KM}km 이내의 주요 장소만 등록할 수 있습니다.`)
      return
    }

    navigate('/setup/3')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={2} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <div className="setup-section-heading">
            <h2>자주 방문하는 주요 장소</h2>
            <p>병원, 복지관, 공원처럼 평소 자주 가는 집 반경 5km 이내의 장소를 등록해 주세요.</p>
          </div>

          <div className="place-list">
            {setup.places.map((place, index) => {
              const isActive = activePlaceIndex === index
              const suggestionId = `place-suggestions-${index}`

              return (
                <div className="place-row" key={`place-${index + 1}`}>
                  <span className="place-number">{index + 1}</span>
                  <div className="place-search-field">
                    <input
                      aria-label={`${index + 1}번째 주요 장소`}
                      value={place}
                      onChange={(event) => updatePlace(index, event.target.value)}
                      onFocus={() => {
                        if (activePlaceIndex !== index) {
                          requestIdRef.current += 1
                          setSuggestions([])
                          setSearchMessage('')
                          setPlaceEdited(false)
                        }
                        setActivePlaceIndex(index)
                      }}
                      onKeyDown={(event) => {
                        if (event.key === 'Escape') {
                          requestIdRef.current += 1
                          setSuggestions([])
                          setSearchMessage('')
                          setPlaceEdited(false)
                        }
                        if (event.key === 'Enter') {
                          event.preventDefault()
                          setPlaceEdited(false)
                          runPlaceSearch(index, place)
                        }
                      }}
                      placeholder="장소명 또는 주소"
                      role="combobox"
                      aria-autocomplete="list"
                      aria-expanded={isActive && suggestions.length > 0}
                      aria-controls={suggestionId}
                      required
                    />

                    {isActive && suggestions.length > 0 && (
                      <ul
                        id={suggestionId}
                        className="location-suggestions place-suggestions"
                        role="listbox"
                        aria-label={`${index + 1}번째 주요 장소 검색 결과`}
                      >
                        {suggestions.map((location) => {
                          const distanceKm = getDistanceKm(setup.homePosition, location)
                          const isOutsideRange = !Number.isFinite(distanceKm)
                            || distanceKm > MAX_PLACE_DISTANCE_KM

                          return (
                            <li key={location.id} role="option" aria-selected="false">
                              <button
                                type="button"
                                onClick={() => selectPlace(index, location)}
                                disabled={isOutsideRange}
                                title={isOutsideRange ? `집 반경 ${MAX_PLACE_DISTANCE_KM}km 밖의 장소입니다.` : undefined}
                              >
                                <strong>{location.name}</strong>
                                <span>{location.address}</span>
                                <em className={isOutsideRange ? 'outside-range' : undefined}>
                                  {formatDistance(distanceKm)}
                                  {isOutsideRange ? ' · 선택 불가' : ''}
                                </em>
                              </button>
                            </li>
                          )
                        })}
                      </ul>
                    )}

                    {isActive && searchMessage && (
                      <p className={`place-search-message location-search-${searchStatus}`} role="status">
                        {searchMessage}
                      </p>
                    )}
                  </div>
                  <button
                    className="remove-place"
                    type="button"
                    onClick={() => removePlace(index)}
                    aria-label={`${index + 1}번째 장소 삭제`}
                  >
                    ×
                  </button>
                </div>
              )
            })}
          </div>

          <button className="add-place" type="button" onClick={addPlace}>＋ 장소 추가</button>

          <div className="setup-map setup-place-map" aria-label="집과 주요 장소 위치 지도">
            <KakaoMap
              currentPosition={setup.homePosition}
              currentMarkerTitle=""
              markers={[
                ...(isCoordinate(setup.homePosition)
                  ? [{ position: setup.homePosition, color: '#3b82f6', title: '집' }]
                  : []),
                ...((setup.placeLocations ?? [])
                  .filter((location) => isCoordinate(location))
                  .map((location) => ({
                    position: location,
                    color: '#22c55e',
                    title: '주요장소',
                  }))),
              ]}
              ariaLabel="집과 주요 장소를 표시한 카카오 지도"
            />
          </div>
        </div>

        <button className="setup-primary-action" type="submit">다음 단계</button>
      </form>
    </main>
  )
}
