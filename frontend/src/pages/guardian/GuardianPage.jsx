import KakaoMap from '../../components/KakaoMap.jsx'
import { NavLink } from 'react-router-dom'

const recentMovements = [
  { time: '오후 2:20', description: '늘봄공원 인근 이동' },
  { time: '오후 1:45', description: '생활문화센터 경로당 방문' },
  { time: '오전 9:10', description: '집에서 외출' },
]

const riskStages = {
  0: {
    label: '0단계 정상',
    summary: '평소 범위 내',
    title: '✓ 정상 이동 중',
    message: '평소 이동패턴과 일치합니다. MOMENT가 계속 분석하고 있으니 안심하세요.',
  },
  1: {
    label: '1단계 주의',
    summary: '평소 범위 확인 중',
    title: '평소와 다른 이동 징후 확인 중',
    message: '일시적으로 평소 경로와 다른 움직임이 감지되어 이동 상태를 다시 확인하고 있습니다.',
  },
  2: {
    label: '2단계 경고',
    summary: '평소 범위 벗어남',
    title: '평소와 다른 이동 징후가 이어지고 있습니다',
    message: '보호자에게 현재 이동 상태를 안내했습니다. 이동 경로를 함께 확인해 주세요.',
  },
  3: {
    label: '3단계 위험',
    summary: '지속 증가 확인',
    title: '보호자 확인이 필요합니다',
    message: '안내 후에도 평소와 다른 이동 징후가 지속되고 있습니다. 현재 상황을 확인해 주세요.',
  },
}

const riskNavigation = [
  { path: '/guardian/normal', label: '정상', level: 0 },
  { path: '/guardian/caution', label: '주의', level: 1 },
  { path: '/guardian/warning', label: '경고', level: 2 },
  { path: '/guardian/danger', label: '위험', level: 3 },
]

export default function GuardianPage({ riskLevel }) {
  const stage = riskStages[riskLevel]

  return (
    <main className={`guardian-page risk-level-${riskLevel}`}>
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
            {stage.label}
          </div>
        </div>
      </header>

      <div className="guardian-content">
        <nav className="risk-tabs" aria-label="위험 단계 화면">
          {riskNavigation.map(({ path, label, level }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
              aria-label={`${level}단계 ${label}`}
            >
              <span>{level}</span>
              {label}
            </NavLink>
          ))}
        </nav>

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
            <span>{stage.summary}</span>
          </article>
          <article className="dashboard-card summary-card">
            <p>집과의 거리</p>
            <strong>840m</strong>
            <span>{stage.summary}</span>
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

        <section className="risk-status" aria-live="polite">
          <h2>{stage.title}</h2>
          <p>{stage.message}</p>
        </section>
      </div>
    </main>
  )
}
