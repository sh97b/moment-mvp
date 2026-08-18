import { loadKakaoMapsSdk } from '../components/KakaoMap.jsx'

const MAX_LOCATION_RESULTS = 6

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

export async function searchKakaoLocations(appKey, rawQuery) {
  const query = rawQuery.trim()
  if (!appKey || query.length < 2) return []

  await loadKakaoMapsSdk(appKey)

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
        .slice(0, MAX_LOCATION_RESULTS)

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
    }, { size: MAX_LOCATION_RESULTS })
  })
}
