import { useEffect, useRef, useState } from 'react'

const KAKAO_MAP_SCRIPT_ID = 'kakao-map-sdk'
const SETUP_PREVIEW_CENTER = { lat: 37.5665, lng: 126.978 }
const ROUTE_PADDING = 44
const KAKAO_MAX_LEVEL = 14
const KAKAO_MIN_LEVEL = 2
const SINGLE_POINT_MAX_LEVEL = 4
const EMPTY_PATH = []

let kakaoMapsPromise

function isCoordinate(position) {
  return Number.isFinite(position?.lat) && Number.isFinite(position?.lng)
}

function isEntireRouteVisible(map, path) {
  if (!map || !window.kakao?.maps) return true

  const coordinates = path.filter(isCoordinate)
  if (coordinates.length < 2) return true

  const bounds = map.getBounds()
  return coordinates.every(({ lat, lng }) =>
    bounds.contain(new window.kakao.maps.LatLng(lat, lng)),
  )
}

function segmentIntersectsViewport(start, end, viewport) {
  const deltaLng = end.lng - start.lng
  const deltaLat = end.lat - start.lat
  const edges = [
    [-deltaLng, start.lng - viewport.west],
    [deltaLng, viewport.east - start.lng],
    [-deltaLat, start.lat - viewport.south],
    [deltaLat, viewport.north - start.lat],
  ]
  let startRatio = 0
  let endRatio = 1

  for (const [direction, distance] of edges) {
    if (direction === 0 && distance < 0) return false
    if (direction === 0) continue

    const ratio = distance / direction
    if (direction < 0) {
      startRatio = Math.max(startRatio, ratio)
    } else {
      endRatio = Math.min(endRatio, ratio)
    }

    if (startRatio > endRatio) return false
  }

  return true
}

function isAnyRouteVisible(map, path) {
  if (!map || !window.kakao?.maps) return true

  const coordinates = path.filter(isCoordinate)
  if (coordinates.length < 2) return true

  const bounds = map.getBounds()
  const southWest = bounds.getSouthWest()
  const northEast = bounds.getNorthEast()
  const viewport = {
    south: southWest.getLat(),
    north: northEast.getLat(),
    west: southWest.getLng(),
    east: northEast.getLng(),
  }

  return coordinates
    .slice(1)
    .some((coordinate, index) =>
      segmentIntersectsViewport(coordinates[index], coordinate, viewport),
    )
}

function getMapView(map) {
  const center = map.getCenter()
  return {
    center: { lat: center.getLat(), lng: center.getLng() },
    level: map.getLevel(),
  }
}

function keepRouteInView(
  map,
  path,
  lastValidViewRef,
  restoringViewRef,
  constraintSuspendedRef,
  routeFitLevelRef,
) {
  if (
    restoringViewRef.current ||
    constraintSuspendedRef.current ||
    path.filter(isCoordinate).length < 2
  ) {
    return
  }

  const isZoomedIn = map.getLevel() < routeFitLevelRef.current
  const isRouteVisible = isZoomedIn
    ? isAnyRouteVisible(map, path)
    : isEntireRouteVisible(map, path)

  if (isRouteVisible) {
    lastValidViewRef.current = getMapView(map)
    return
  }

  const lastValidView = lastValidViewRef.current
  if (!lastValidView) return

  restoringViewRef.current = true
  map.setLevel(lastValidView.level)
  map.setCenter(
    new window.kakao.maps.LatLng(
      lastValidView.center.lat,
      lastValidView.center.lng,
    ),
  )
  window.requestAnimationFrame(() => {
    restoringViewRef.current = false
  })
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

export function loadKakaoMapsSdk(appKey) {
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
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(appKey)}&autoload=false&libraries=services`
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

export default function KakaoMap({
  currentPosition = null,
  path = EMPTY_PATH,
  markers = EMPTY_PATH,
  ariaLabel = '현재 frame 위치와 지금까지의 합성 이동 경로를 표시한 카카오 지도',
  interactive = true,
}) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const markerRefsRef = useRef([])
  const polylineRef = useRef(null)
  const latestPositionRef = useRef(currentPosition)
  const latestPathRef = useRef(path)
  const lastValidViewRef = useRef(null)
  const restoringViewRef = useRef(false)
  const constraintSuspendedRef = useRef(false)
  const routeFitLevelRef = useRef(SINGLE_POINT_MAX_LEVEL)
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
    let mapInstance
    let handleViewportChange

    loadKakaoMapsSdk(appKey)
      .then(() => {
        if (!isMounted || !mapContainerRef.current) return

        const initialPosition = isCoordinate(latestPositionRef.current)
          ? latestPositionRef.current
          : SETUP_PREVIEW_CENTER
        const center = new window.kakao.maps.LatLng(initialPosition.lat, initialPosition.lng)
        const map = new window.kakao.maps.Map(mapContainerRef.current, {
          center,
          level: interactive ? 4 : 3,
        })
        map.setZoomable(interactive)
        map.setDraggable(interactive)
        map.setKeyboardShortcuts(interactive)
        if (!interactive) {
          map.setMinLevel(3)
          map.setMaxLevel(3)
        } else {
          map.setMinLevel(KAKAO_MIN_LEVEL)
        }
        if (interactive) {
          fitMapToRoute(map, latestPathRef.current, latestPositionRef.current)
          routeFitLevelRef.current = map.getLevel()
          lastValidViewRef.current = getMapView(map)
        } else {
          map.setCenter(center)
          routeFitLevelRef.current = map.getLevel()
          lastValidViewRef.current = getMapView(map)
        }
        mapInstance = map
        handleViewportChange = () => {
          keepRouteInView(
            map,
            latestPathRef.current,
            lastValidViewRef,
            restoringViewRef,
            constraintSuspendedRef,
            routeFitLevelRef,
          )
        }
        window.kakao.maps.event.addListener(
          map,
          'center_changed',
          handleViewportChange,
        )
        window.kakao.maps.event.addListener(
          map,
          'zoom_changed',
          handleViewportChange,
        )

        mapRef.current = map
        if (typeof ResizeObserver !== 'undefined') {
          resizeObserver = new ResizeObserver(() => {
            map.relayout()
            window.cancelAnimationFrame(resizeFrame)
            resizeFrame = window.requestAnimationFrame(() => {
              constraintSuspendedRef.current = true
              fitMapToRoute(map, latestPathRef.current, latestPositionRef.current)
              routeFitLevelRef.current = map.getLevel()
              lastValidViewRef.current = getMapView(map)
              window.requestAnimationFrame(() => {
                constraintSuspendedRef.current = false
              })
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
      if (mapInstance && handleViewportChange && window.kakao?.maps?.event) {
        window.kakao.maps.event.removeListener(
          mapInstance,
          'center_changed',
          handleViewportChange,
        )
        window.kakao.maps.event.removeListener(
          mapInstance,
          'zoom_changed',
          handleViewportChange,
        )
      }
      markerRef.current?.setMap(null)
      markerRefsRef.current.forEach((marker) => marker.setMap(null))
      polylineRef.current?.setMap(null)
      markerRef.current = null
      markerRefsRef.current = []
      polylineRef.current = null
      mapRef.current = null
    }
  }, [appKey, interactive])

  useEffect(() => {
    const map = mapRef.current
    if (status !== 'ready' || !map || !window.kakao?.maps) return

    const explicitMarkers = Array.isArray(markers)
      ? markers.filter(({ position }) => isCoordinate(position))
      : []

    markerRefsRef.current.forEach((marker) => marker.setMap(null))
    markerRefsRef.current = []

    if (explicitMarkers.length > 0) {
      markerRef.current?.setMap(null)
      markerRef.current = null
      markerRefsRef.current = explicitMarkers.map(({
        position,
        color = '#2d6cdf',
        title,
      }) => new window.kakao.maps.Marker({
        map,
        position: new window.kakao.maps.LatLng(position.lat, position.lng),
        title,
        image: new window.kakao.maps.MarkerImage(
          `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
            <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">
              <circle cx="11" cy="11" r="9" fill="${color}" stroke="#ffffff" stroke-width="3"/>
            </svg>
          `)}`,
          new window.kakao.maps.Size(22, 22),
          { offset: new window.kakao.maps.Point(11, 11) },
        ),
      }))

      if (explicitMarkers.length === 1) {
        const [{ position }] = explicitMarkers
        map.setCenter(new window.kakao.maps.LatLng(position.lat, position.lng))
      } else {
        const bounds = new window.kakao.maps.LatLngBounds()
        explicitMarkers.forEach(({ position }) => {
          bounds.extend(new window.kakao.maps.LatLng(position.lat, position.lng))
        })
        map.setBounds(bounds, 36, 36, 36, 36)
      }
      constraintSuspendedRef.current = true
      routeFitLevelRef.current = map.getLevel()
      lastValidViewRef.current = getMapView(map)
      window.requestAnimationFrame(() => {
        constraintSuspendedRef.current = false
      })
      return
    }

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
    } else if (markerRef.current) {
      markerRef.current.setMap(null)
      markerRef.current = null
    }

    const linePath = path
      .filter(isCoordinate)
      .map(({ lat, lng }) => new window.kakao.maps.LatLng(lat, lng))

    if (!interactive && isCoordinate(currentPosition)) {
      const focusedCenter = new window.kakao.maps.LatLng(currentPosition.lat, currentPosition.lng)
      map.setCenter(focusedCenter)
      map.setLevel(3)
      map.setMinLevel(3)
      map.setMaxLevel(3)
      constraintSuspendedRef.current = true
      routeFitLevelRef.current = map.getLevel()
      lastValidViewRef.current = getMapView(map)
      window.requestAnimationFrame(() => {
        constraintSuspendedRef.current = false
      })
    } else {
      constraintSuspendedRef.current = true
      fitMapToRoute(map, path, currentPosition)
      routeFitLevelRef.current = map.getLevel()
      lastValidViewRef.current = getMapView(map)
      window.requestAnimationFrame(() => {
        constraintSuspendedRef.current = false
      })
    }

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
  }, [currentPosition, path, markers, status, interactive])

  return (
    <div className="guardian-map-wrapper">
      <div
        ref={mapContainerRef}
        className="guardian-map"
        role="img"
        aria-label={ariaLabel}
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
