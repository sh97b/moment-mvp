import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { searchKakaoLocations } from '../../utils/kakaoLocationSearch.js'

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
    requestIdRef.current += 1
    updateField('places', setup.places.map((place, itemIndex) => (
      itemIndex === index ? location.name : place
    )))
    updatePlaceLocation(index, {
      name: location.name,
      address: location.address,
      lat: location.lat,
      lng: location.lng,
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
    navigate('/setup/3')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={2} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <div className="setup-section-heading">
            <h2>자주 방문하는 주요 장소</h2>
            <p>병원, 복지관, 공원처럼 평소 자주 가는 데모용 장소를 검색해 등록해 주세요.</p>
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
                        {suggestions.map((location) => (
                          <li key={location.id} role="option" aria-selected="false">
                            <button type="button" onClick={() => selectPlace(index, location)}>
                              <strong>{location.name}</strong>
                              <span>{location.address}</span>
                            </button>
                          </li>
                        ))}
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
        </div>

        <button className="setup-primary-action" type="submit">다음 단계</button>
      </form>
    </main>
  )
}
