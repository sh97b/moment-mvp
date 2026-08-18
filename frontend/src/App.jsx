import { Navigate, Route, Routes } from 'react-router-dom'
import { GuardianSetupProvider } from './context/GuardianSetupContext.jsx'
import GuardianReplayPage from './pages/guardian/GuardianReplayPage.jsx'
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
        <Route path="/" element={<SetupPage />} />
        <Route path="/setup" element={<SetupPage />} />
        <Route path="/setup/guardian" element={<Navigate to="/setup/1" replace />} />
        <Route path="/setup/1" element={<GuardianSetupBasicPage />} />
        <Route path="/setup/2" element={<GuardianSetupPlacesPage />} />
        <Route path="/setup/3" element={<GuardianSetupPatternPage />} />
        <Route path="/setup/4" element={<GuardianSetupCompletePage />} />
        <Route path="/guardian" element={<GuardianReplayPage />} />
        <Route path="/guardian/normal" element={<Navigate to="/guardian?scenario=normal" replace />} />
        <Route path="/guardian/caution" element={<Navigate to="/guardian?scenario=temporary_return" replace />} />
        <Route path="/guardian/warning" element={<Navigate to="/guardian?scenario=persistent_anomaly" replace />} />
        <Route path="/guardian/danger" element={<Navigate to="/guardian?scenario=persistent_anomaly" replace />} />
        <Route path="/senior" element={<SeniorPage />} />
        <Route path="*" element={<Navigate to="/setup" replace />} />
      </Routes>
    </GuardianSetupProvider>
  )
}
