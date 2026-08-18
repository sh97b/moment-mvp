import { useEffect, useRef, useState } from 'react'

const KAKAO_MAP_SCRIPT_ID = 'kakao-map-sdk'
const SETUP_PREVIEW_CENTER = { lat: 37.5665, lng: 126.978 }
const ROUTE_PADDING = 44
const KAKAO_MAX_LEVEL = 14
const SINGLE_POINT_MAX_LEVEL = 4

let kakaoMapsPromise

function isCoordinate(position) {
  return Number.isFinite(position?.lat) && Number.isFinite(position?.lng)
}

function fitMapToRoute(map, path, currentPosition) {
  if (!map || !window.kakao?.maps) return

  const coordinates = path.filter(isCoordinate)
  if (coordinates.length >= 2) {
    // 이전 경로의 제한을 먼저 풀어 새 누적 경로에 맞는 레벨을 계산한다.
    map.setMaxLevel(KAKAO_MAX_LEVEL)
    const bounds = new window.kakao.maps.LatLngBounds()
    coordinates.forEach(({ lat, lng }) => {
      bounds.extend(new window.kakao.maps.LatLng(lat, lng))
    })
    map.setBounds(
      bounds,
      ROUTE_PADDING,
      ROUTE_PADDING,
      ROUTE_PADDING,
      ROUTE_PADDING,
    )
    map.setMaxLevel(map.getLevel())
    return
  }

  if (isCoordinate(currentPosition)) {
    map.setCenter(new window.kakao.maps.LatLng(currentPosition.lat, currentPosition.lng))
    map.setMaxLevel(SINGLE_POINT_MAX_LEVEL)
  }
}

function loadKakaoMapsSdk(appKey) {
  if (window.kakao?.maps) {
    return new Promise((resolve) => window.kakao.maps.load(resolve))
  }

  if (kakaoMapsPromise) return kakaoMapsPromise

  kakaoMapsPromise = new Promise((resolve, reject) => {
    const loadMaps = () => {
      if (!window.kakao?.maps) {
        reject(new Error('Kakao Maps SDK를 불러오지 못했습니다.'))
        return
      }
      window.kakao.maps.load(resolve)
    }

    const existingScript = document.getElementById(KAKAO_MAP_SCRIPT_ID)
    if (existingScript) {
      existingScript.addEventListener('load', loadMaps, { once: true })
      existingScript.addEventListener(
        'error',
        () => reject(new Error('Kakao Maps SDK 요청에 실패했습니다.')),
        { once: true },
      )
      return
    }

    const script = document.createElement('script')
    script.id = KAKAO_MAP_SCRIPT_ID
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(appKey)}&autoload=false`
    script.async = true
    script.addEventListener('load', loadMaps, { once: true })
    script.addEventListener(
      'error',
      () => reject(new Error('Kakao Maps SDK 요청에 실패했습니다.')),
      { once: true },
    )
    document.head.appendChild(script)
  })

  return kakaoMapsPromise
}

export default function KakaoMap({ currentPosition = null, path = [] }) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const polylineRef = useRef(null)
  const latestPositionRef = useRef(currentPosition)
  const latestPathRef = useRef(path)
  const [status, setStatus] = useState('loading')
  const appKey = import.meta.env.VITE_KAKAO_MAP_KEY?.trim()

  latestPositionRef.current = currentPosition
  latestPathRef.current = path

  useEffect(() => {
    if (!appKey) {
      setStatus('missing-key')
      return undefined
    }

    let isMounted = true
    let resizeObserver
    let resizeFrame

    loadKakaoMapsSdk(appKey)
      .then(() => {
        if (!isMounted || !mapContainerRef.current) return

        const initialPosition = isCoordinate(latestPositionRef.current)
          ? latestPositionRef.current
          : SETUP_PREVIEW_CENTER
        const center = new window.kakao.maps.LatLng(initialPosition.lat, initialPosition.lng)
        const map = new window.kakao.maps.Map(mapContainerRef.current, {
          center,
          level: 4,
        })
        map.setZoomable(true)

        mapRef.current = map
        if (typeof ResizeObserver !== 'undefined') {
          resizeObserver = new ResizeObserver(() => {
            map.relayout()
            window.cancelAnimationFrame(resizeFrame)
            resizeFrame = window.requestAnimationFrame(() => {
              fitMapToRoute(map, latestPathRef.current, latestPositionRef.current)
            })
          })
          resizeObserver.observe(mapContainerRef.current)
        }
        setStatus('ready')
      })
      .catch(() => {
        if (isMounted) setStatus('error')
      })

    return () => {
      isMounted = false
      resizeObserver?.disconnect()
      window.cancelAnimationFrame(resizeFrame)
      markerRef.current?.setMap(null)
      polylineRef.current?.setMap(null)
      markerRef.current = null
      polylineRef.current = null
      mapRef.current = null
    }
  }, [appKey])

  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map || !window.kakao?.maps) return

    if (isCoordinate(currentPosition)) {
      const markerPosition = new window.kakao.maps.LatLng(
        currentPosition.lat,
        currentPosition.lng,
      )

      if (!markerRef.current) {
        markerRef.current = new window.kakao.maps.Marker({
          map,
          position: markerPosition,
        })
      } else {
        markerRef.current.setPosition(markerPosition)
      }
    }

    const linePath = path
      .filter(isCoordinate)
      .map(({ lat, lng }) => new window.kakao.maps.LatLng(lat, lng))

    fitMapToRoute(map, path, currentPosition)

    if (!polylineRef.current && linePath.length >= 2) {
      polylineRef.current = new window.kakao.maps.Polyline({
        map,
        path: linePath,
        strokeWeight: 5,
        strokeColor: '#3f5fa9',
        strokeOpacity: 0.85,
        strokeStyle: 'solid',
      })
    } else if (polylineRef.current) {
      polylineRef.current.setPath(linePath)
    }
  }, [currentPosition, path, status])

  return (
    <div className="guardian-map-wrapper">
      <div
        ref={mapContainerRef}
        className="guardian-map"
        role="img"
        aria-label="현재 frame 위치와 지금까지의 합성 이동 경로를 표시한 카카오 지도"
      />

      {status !== 'ready' && (
        <div className="map-fallback" role="status">
          {status === 'missing-key' && (
            <>
              <strong>카카오맵 API 키가 필요합니다</strong>
              <span>frontend/.env의 VITE_KAKAO_MAP_KEY를 입력해 주세요.</span>
            </>
          )}
          {status === 'loading' && <span>지도를 불러오는 중입니다.</span>}
          {status === 'error' && (
            <>
              <strong>지도를 불러오지 못했습니다</strong>
              <span>API 키와 등록된 도메인을 확인해 주세요.</span>
            </>
          )}
        </div>
      )}
    </div>
  )
}
