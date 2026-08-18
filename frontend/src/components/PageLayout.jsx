import { NavLink } from 'react-router-dom'

const navigation = [
  { path: '/setup', label: '생활패턴 설정' },
  { path: '/guardian', label: '보호자 모니터링' },
]

export default function PageLayout({ title, description }) {
  return (
    <main className="page-layout">
      <p className="eyebrow">MOMENT MVP</p>
      <h1>{title}</h1>
      <p>{description}</p>

      <nav aria-label="주요 페이지">
        {navigation.map(({ path, label }) => (
          <NavLink
            key={path}
            className={({ isActive }) => (isActive ? 'active' : undefined)}
            to={path}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      <small>
        API: {import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}
      </small>
    </main>
  )
}
