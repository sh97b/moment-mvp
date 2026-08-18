import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'

const returnTimes = [
  ['15:00', '오후 3시'],
  ['16:00', '오후 4시'],
  ['17:00', '오후 5시'],
  ['18:00', '오후 6시'],
  ['19:00', '오후 7시'],
  ['20:00', '오후 8시'],
]

const patternSuggestions = [
  ['오전 산책', '오전 산책을 자주 합니다.'],
  ['복지관 방문', '복지관에 정기적으로 방문합니다.'],
  ['병원 방문', '정해진 요일에 병원을 방문합니다.'],
  ['장보기', '주중에 장을 보러 외출합니다.'],
]

export default function GuardianSetupPatternPage() {
  const navigate = useNavigate()
  const { setup, updateField } = useGuardianSetup()

  const addSuggestion = (sentence) => {
    const separator = setup.lifePattern.trim() ? ' ' : ''
    updateField('lifePattern', `${setup.lifePattern.trim()}${separator}${sentence}`)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    navigate('/setup/4')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={3} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <aside className="setup-ai-box">
            <span aria-hidden="true">✦</span>
            <div>
              <strong>AI가 평소 생활패턴을 이해해요</strong>
              <p>귀가 시간과 자유롭게 적어주신 생활패턴을 구조화해 초기 Context를 구성합니다.</p>
            </div>
          </aside>

          <fieldset className="return-time-field">
            <legend>평소 귀가 시간</legend>
            <div className="return-time-grid">
              {returnTimes.map(([value, label]) => (
                <button
                  key={value}
                  className={setup.returnTime === value ? 'active' : undefined}
                  type="button"
                  onClick={() => updateField('returnTime', value)}
                >
                  {label}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="setup-field pattern-field">
            <span>평소 생활패턴</span>
            <small>자주 외출하는 시간, 산책 습관, 방문 요일 등을 자연스럽게 적어주세요.</small>
            <textarea
              value={setup.lifePattern}
              onChange={(event) => updateField('lifePattern', event.target.value)}
              rows="6"
              required
            />
          </label>

          <div className="pattern-suggestions" aria-label="생활패턴 문구 추가">
            {patternSuggestions.map(([label, sentence]) => (
              <button key={label} type="button" onClick={() => addSuggestion(sentence)}>
                ＋ {label}
              </button>
            ))}
          </div>
        </div>

        <button className="setup-primary-action" type="submit">AI로 초기 Context 구성하기</button>
      </form>
    </main>
  )
}
