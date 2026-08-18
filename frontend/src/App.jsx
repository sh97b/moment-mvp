import { Navigate, Route, Routes } from 'react-router-dom'
import { GuardianSetupProvider } from './context/GuardianSetupContext.jsx'
import GuardianCautionPage from './pages/guardian/GuardianCautionPage.jsx'
import GuardianDangerPage from './pages/guardian/GuardianDangerPage.jsx'
import GuardianNormalPage from './pages/guardian/GuardianNormalPage.jsx'
import GuardianWarningPage from './pages/guardian/GuardianWarningPage.jsx'
import GuardianSetupBasicPage from './pages/setup/GuardianSetupBasicPage.jsx'
import GuardianSetupCompletePage from './pages/setup/GuardianSetupCompletePage.jsx'
import GuardianSetupPatternPage from './pages/setup/GuardianSetupPatternPage.jsx'
import GuardianSetupPlacesPage from './pages/setup/GuardianSetupPlacesPage.jsx'
import SetupPage from './pages/setup/SetupPage.jsx'
import SeniorPage from './pages/senior/SeniorPage.jsx'

export default function App() {
  return (
    <GuardianSetupProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/setup" replace />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/setup/guardian" element={<Navigate to="/setup/guardian/basic" replace />} />
        <Route path="/setup/guardian/basic" element={<GuardianSetupBasicPage />} />
        <Route path="/setup/guardian/places" element={<GuardianSetupPlacesPage />} />
        <Route path="/setup/guardian/pattern" element={<GuardianSetupPatternPage />} />
        <Route path="/setup/guardian/complete" element={<GuardianSetupCompletePage />} />
        <Route path="/guardian" element={<Navigate to="/guardian/normal" replace />} />
        <Route path="/guardian/normal" element={<GuardianNormalPage />} />
        <Route path="/guardian/caution" element={<GuardianCautionPage />} />
        <Route path="/guardian/warning" element={<GuardianWarningPage />} />
        <Route path="/guardian/danger" element={<GuardianDangerPage />} />
        <Route path="/senior" element={<SeniorPage />} />
        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Routes>
    </GuardianSetupProvider>
  )
}
