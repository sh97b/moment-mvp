import { useNavigate } from 'react-router-dom'
import GuardianSetupHeader from '../../components/GuardianSetupHeader.jsx'
import { useGuardianSetup } from '../../context/GuardianSetupContext.jsx'

export default function GuardianSetupPlacesPage() {
  const navigate = useNavigate()
  const { setup, updateField } = useGuardianSetup()

  const updatePlace = (index, value) => {
    updateField('places', setup.places.map((place, itemIndex) => (
      itemIndex === index ? value : place
    )))
  }

  const removePlace = (index) => {
    updateField('places', setup.places.filter((_, itemIndex) => itemIndex !== index))
  }

  const addPlace = () => {
    updateField('places', [...setup.places, ''])
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    navigate('/setup/guardian/pattern')
  }

  return (
    <main className="guardian-setup-page">
      <GuardianSetupHeader step={2} />

      <form className="setup-form" onSubmit={handleSubmit}>
        <div className="setup-form-content">
          <div className="setup-section-heading">
            <h2>자주 방문하는 주요 장소</h2>
            <p>병원, 복지관, 공원처럼 평소 자주 가는 합성 장소를 등록해 주세요.</p>
          </div>

          <div className="place-list">
            {setup.places.map((place, index) => (
              <div className="place-row" key={`place-${index + 1}`}>
                <span className="place-number">{index + 1}</span>
                <input
                  aria-label={`${index + 1}번째 주요 장소`}
                  value={place}
                  onChange={(event) => updatePlace(index, event.target.value)}
                  placeholder="합성 장소 이름"
                  required
                />
                <button
                  className="remove-place"
                  type="button"
                  onClick={() => removePlace(index)}
                  aria-label={`${index + 1}번째 장소 삭제`}
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <button className="add-place" type="button" onClick={addPlace}>＋ 장소 추가</button>
        </div>

        <button className="setup-primary-action" type="submit">다음 단계</button>
      </form>
    </main>
  )
}
