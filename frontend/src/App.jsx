import { Navigate, Route, Routes } from 'react-router-dom'
import GuardianPage from './pages/GuardianPage.jsx'
import SeniorPage from './pages/SeniorPage.jsx'
import SetupPage from './pages/SetupPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/setup" replace />} />
      <Route path="/setup" element={<SetupPage />} />
      <Route path="/guardian" element={<GuardianPage />} />
      <Route path="/senior" element={<SeniorPage />} />
      <Route path="*" element={<Navigate to="/setup" replace />} />
    </Routes>
  )
}
