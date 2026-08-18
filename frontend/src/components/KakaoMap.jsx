import { useEffect, useRef, useState } from 'react'

const KAKAO_MAP_SCRIPT_ID = 'kakao-map-sdk'
const DEMO_CENTER = { lat: 33.450701, lng: 126.570667 }

let kakaoMapsPromise

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

export default function KakaoMap() {
  const mapContainerRef = useRef(null)
  const [status, setStatus] = useState('loading')
  const appKey = import.meta.env.VITE_KAKAO_MAP_KEY?.trim()

  useEffect(() => {
    if (!appKey) {
      setStatus('missing-key')
      return undefined
    }

    let isMounted = true
    let resizeObserver

    loadKakaoMapsSdk(appKey)
      .then(() => {
        if (!isMounted || !mapContainerRef.current) return

        const center = new window.kakao.maps.LatLng(DEMO_CENTER.lat, DEMO_CENTER.lng)
        const map = new window.kakao.maps.Map(mapContainerRef.current, {
          center,
          level: 4,
        })

        resizeObserver = new ResizeObserver(() => {
          map.relayout()
          map.setCenter(center)
        })
        resizeObserver.observe(mapContainerRef.current)
        setStatus('ready')
      })
      .catch(() => {
        if (isMounted) setStatus('error')
      })

    return () => {
      isMounted = false
      resizeObserver?.disconnect()
    }
  }, [appKey])

  return (
    <div className="guardian-map-wrapper">
      <div
        ref={mapContainerRef}
        className="guardian-map"
        aria-label="카카오 지도"
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
