import KakaoMap from '../components/KakaoMap.jsx'

const recentMovements = [
  { time: '오후 2:20', description: '늘봄공원 인근 이동' },
  { time: '오후 1:45', description: '생활문화센터 경로당 방문' },
  { time: '오전 9:10', description: '집에서 외출' },
]

export default function GuardianPage() {
  return (
    <main className="guardian-page">
      <header className="guardian-hero">
        <div className="guardian-brand-row">
          <div className="guardian-brand" aria-label="MOMENT">
            <span className="guardian-brand-mark">M</span>
            <span>MOMENT</span>
          </div>
          <div className="live-badge">
            <span className="status-dot" />
            실시간 분석 중
          </div>
        </div>

        <div className="guardian-person-row">
          <div>
            <p className="guardian-label">보호 대상자</p>
            <h1>보호 대상자 A</h1>
          </div>
          <div className="risk-badge">
            <span className="status-dot" />
            0단계 정상
          </div>
        </div>
      </header>

      <div className="guardian-content">
        <section className="dashboard-card map-card" aria-labelledby="location-title">
          <div className="card-heading">
            <h2 id="location-title">현재 위치 및 이동 경로</h2>
            <time dateTime="14:34">오후 2:34 기준</time>
          </div>
          <KakaoMap />
        </section>

        <section className="summary-grid" aria-label="현재 이동 요약">
          <article className="dashboard-card summary-card">
            <p>현재 외출 시간</p>
            <strong>2시간 18분</strong>
            <span>평소 범위 내</span>
          </article>
          <article className="dashboard-card summary-card">
            <p>집과의 거리</p>
            <strong>840m</strong>
            <span>평소 범위 내</span>
          </article>
        </section>

        <section className="dashboard-card activity-card" aria-labelledby="activity-title">
          <h2 id="activity-title">최근 이동 상태</h2>
          <ol className="activity-list">
            {recentMovements.map(({ time, description }) => (
              <li key={time}>
                <time>{time}</time>
                <span>{description}</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="normal-status" aria-label="정상 이동 상태">
          <h2>✓ 정상 이동 중</h2>
          <p>평소 이동패턴과 일치합니다. MOMENT가 계속 분석하고 있으니 안심하세요.</p>
        </section>
      </div>
    </main>
  )
}
