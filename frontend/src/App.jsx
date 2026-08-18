import { Navigate, Route, Routes } from 'react-router-dom'
import GuardianCautionPage from './pages/GuardianCautionPage.jsx'
import GuardianDangerPage from './pages/GuardianDangerPage.jsx'
import GuardianNormalPage from './pages/GuardianNormalPage.jsx'
import GuardianWarningPage from './pages/GuardianWarningPage.jsx'
import SeniorPage from './pages/SeniorPage.jsx'
import SetupPage from './pages/SetupPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/setup" replace />} />
      <Route path="/setup" element={<SetupPage />} />
      <Route path="/guardian" element={<Navigate to="/guardian/normal" replace />} />
      <Route path="/guardian/normal" element={<GuardianNormalPage />} />
      <Route path="/guardian/caution" element={<GuardianCautionPage />} />
      <Route path="/guardian/warning" element={<GuardianWarningPage />} />
      <Route path="/guardian/danger" element={<GuardianDangerPage />} />
      <Route path="/senior" element={<SeniorPage />} />
      <Route path="*" element={<Navigate to="/setup" replace />} />
    </Routes>
  )
}
