export default function GuardianSetupHeader({ step, complete = false }) {
  return (
    <header className="setup-header">
      <div className="setup-brand" aria-label="MOMENT">
        <span>M</span>
        MOMENT
      </div>

      <h1>{complete ? '초기 Context가 준비됐어요' : '초기 설정'}</h1>
      <p>
        {complete
          ? '입력한 생활 정보를 초기 이동 Context로 정리했습니다.'
          : '평소 생활 정보를 알려주시면 초기 이동 Context를 구성합니다.'}
      </p>

      {!complete && (
        <div className="setup-progress" aria-label={`초기 설정 ${step}/3 단계`}>
          <div className="setup-progress-bars" aria-hidden="true">
            {[1, 2, 3].map((item) => (
              <span key={item} className={item <= step ? 'active' : undefined} />
            ))}
          </div>
          <span>{step}/3 단계</span>
        </div>
      )}
    </header>
  )
}
