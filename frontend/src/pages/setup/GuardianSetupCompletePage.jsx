import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'
import { createGuardianProfile } from '../../utils/guardianProfile.js'

function formatReturnTime(value) {
  const hour = Number(value.split(':')[0])
  const period = hour < 12 ? '오전' : '오후'
  const displayHour = hour > 12 ? hour - 12 : hour
  return `${period} ${displayHour}시 이전`
}

export default function GuardianSetupCompletePage() {
  const navigate = useNavigate()
  const { setup } = useGuardianSetup()
  const [generatedProfile, setGeneratedProfile] = useState(null)

  const handleStart = () => {
    const profile = generatedProfile ?? createGuardianProfile(setup.personName)
    setGeneratedProfile(profile)
    if (profile?.code) {
      window.localStorage.setItem('moment.last-guardian-profile', JSON.stringify(profile))
    }
    navigate('/guardian')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader complete />

      <div className="setup-complete-body">
        <section className="context-summary" aria-labelledby="context-person-name">
          <div className="context-summary-heading">
            <div>
              <span>보호 대상자</span>
              <h2 id="context-person-name">{setup.personName}</h2>
            </div>
            <strong>Context 생성 완료</strong>
          </div>

          <dl>
            <div>
              <dt>생활 기준 위치</dt>
              <dd>{setup.homeLocation}</dd>
            </div>
            <div>
              <dt>주요 방문 장소</dt>
              <dd>{setup.places.filter(Boolean).join(' · ') || '등록된 장소 없음'}</dd>
            </div>
            <div>
              <dt>등록 코드</dt>
              <dd>{generatedProfile?.code ?? '시작하기를 눌러 생성'}</dd>
            </div>
            <div>
              <dt>평소 귀가 시간</dt>
              <dd>{formatReturnTime(setup.returnTime)}</dd>
            </div>
            <div>
              <dt>생활패턴 요약</dt>
              <dd>{setup.lifePattern}</dd>
            </div>
          </dl>
        </section>

        <aside className="context-notice">
          <strong>이 Context는 초기 기준입니다</strong>
          <p>합성 이동 기록이 쌓이면 GPS Feature를 기반으로 개인 정상 이동 Baseline을 별도로 구성합니다. AI가 위험 여부를 직접 결정하지는 않습니다.</p>
        </aside>

        <button type="button" className="setup-primary-action" onClick={handleStart}>MOMENT 시작하기</button>
      </div>
    </main>
  )
}
