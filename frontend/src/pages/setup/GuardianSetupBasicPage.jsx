import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import KakaoMap from '../../components/KakaoMap.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'

export default function GuardianSetupBasicPage() {
  const navigate = useNavigate()
  const { setup, updateField } = useGuardianSetup()

  const handleSubmit = (event) => {
    event.preventDefault()
    navigate('/setup/guardian/places')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={1} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <aside className="setup-info-box">
            <strong>보호 대상자 기본 정보</strong>
            <p>집 위치는 이후 이동 거리와 귀가 방향을 판단하는 합성 기준으로 사용됩니다.</p>
          </aside>

          <label className="setup-field">
            <span>보호 대상자 표시 이름</span>
            <input
              value={setup.personName}
              onChange={(event) => updateField('personName', event.target.value)}
              placeholder="합성 표시 이름을 입력해 주세요"
              required
            />
          </label>

          <div className="setup-field">
            <label htmlFor="home-location">집 위치</label>
            <div className="location-input-row">
              <input
                id="home-location"
                value={setup.homeLocation}
                onChange={(event) => updateField('homeLocation', event.target.value)}
                placeholder="합성 위치만 입력해 주세요"
                required
              />
              <button type="button">위치 검색</button>
            </div>
            <div className="setup-map">
              <KakaoMap />
            </div>
          </div>
        </div>

        <button className="setup-primary-action" type="submit">다음 단계</button>
      </form>
    </main>
  )
}
