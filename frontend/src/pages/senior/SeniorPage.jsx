import { Link } from 'react-router-dom'

export default function SeniorPage() {
  return (
    <main className="role-page senior-entry-page">
      <header className="role-header">
        <div className="role-brand" aria-label="MOMENT">
          <span>M</span>
          MOMENT
        </div>
      </header>

      <section className="role-content senior-entry-content" aria-labelledby="senior-title">
        <p className="role-eyebrow">고령자 화면</p>
        <h1 id="senior-title">실시간 이동을<br />분석 중입니다</h1>
        <p className="role-description">평소와 다른 이동 징후가 확인되면 화면에 안내해 드립니다.</p>
        <Link className="senior-back-link" to="/setup">사용자 유형 다시 선택</Link>
      </section>
    </main>
  )
}
