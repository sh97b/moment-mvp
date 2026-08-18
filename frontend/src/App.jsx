const pages = {
  '/setup': ['생활패턴 설정', '보호자가 평소 이동 시간과 장소를 입력하는 화면입니다.'],
  '/guardian': ['보호자 모니터링', '이동 경로와 현재 위험 단계를 확인하는 화면입니다.'],
  '/senior': ['안심 안내', '고령자에게 현재 상황과 다음 행동을 안내하는 화면입니다.'],
}

export default function App() {
  const [title, description] = pages[window.location.pathname] ?? ['MOMENT', '인지저하 고령자의 이상 이동을 조기에 발견하는 데모입니다.']
  return <main><p className="eyebrow">MOMENT MVP</p><h1>{title}</h1><p>{description}</p><nav>{Object.entries(pages).map(([path, [label]]) => <a key={path} href={path}>{label}</a>)}</nav><small>API: {import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}</small></main>
}
