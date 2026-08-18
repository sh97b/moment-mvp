import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { findGuardianProfileByCode, normalizeRegistrationCode } from '../../utils/guardianProfile.js'

export default function SeniorEntryPage() {
  const navigate = useNavigate()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()

    const normalizedCode = normalizeRegistrationCode(code)
    if (!normalizedCode || normalizedCode.length !== 5) {
      setError('등록 코드를 5글자로 입력해 주세요.')
      return
    }

    const profile = findGuardianProfileByCode(normalizedCode)
    if (!profile) {
      setError('등록된 보호자 코드가 없거나 올바르지 않습니다.')
      return
    }

    localStorage.setItem('moment.active-guardian-profile', JSON.stringify({
      code: profile.code,
      name: profile.name,
      createdAt: profile.createdAt,
    }))
    navigate('/senior')
  }

  return (
    <main className="replay-state-page">
      <div className="replay-state-brand"><span>M</span>MOMENT</div>
      <section className="senior-entry-card" aria-labelledby="senior-entry-title">
        <p className="senior-entry-label">보호자 코드 입력</p>
        <h1 id="senior-entry-title">고령자 화면 시작</h1>
        <p className="senior-entry-copy">보호자가 알려준 5자리 등록 코드를 입력하면 보호 대상자 이름과 상태를 확인할 수 있습니다.</p>

        <form onSubmit={handleSubmit} className="senior-entry-form">
          <input
            type="text"
            inputMode="text"
            maxLength={5}
            value={code}
            onChange={(event) => {
              setCode(event.target.value)
              setError('')
            }}
            placeholder="예: ABC12"
            aria-label="등록 코드"
          />

          <button type="submit">확인</button>
        </form>

        {error && <p className="senior-entry-error" role="alert">{error}</p>}
      </section>
    </main>
  )
}
