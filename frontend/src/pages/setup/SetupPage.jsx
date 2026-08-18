import { Link } from 'react-router-dom'

export default function SetupPage() {
  return (
    <main className="role-page">
      <header className="role-header">
        <div className="role-brand" aria-label="MOMENT">
          <span>M</span>
          MOMENT
        </div>
      </header>

      <section className="role-content" aria-labelledby="role-title">
        <p className="role-eyebrow">시작하기</p>
        <h1 id="role-title">사용자 유형 선택</h1>
        <p className="role-description">사용자의 유형을 골라주세요</p>

        <nav className="role-actions" aria-label="사용자 유형 선택">
          <Link className="role-button guardian-role" to="/setup/guardian/basic">
            <span className="role-icon" aria-hidden="true">보</span>
            <span className="role-button-copy">
              <strong>보호자</strong>
              <small>이동 상태 확인하기</small>
            </span>
            <span className="role-arrow" aria-hidden="true">→</span>
          </Link>

          <Link className="role-button senior-role" to="/senior">
            <span className="role-icon" aria-hidden="true">고</span>
            <span className="role-button-copy">
              <strong>고령자</strong>
              <small>안심 안내 확인하기</small>
            </span>
            <span className="role-arrow" aria-hidden="true">→</span>
          </Link>
        </nav>
      </section>

      <footer className="role-footer">
        평소와 다른 이동 징후를 함께 살펴봅니다.
      </footer>
    </main>
  )
}
