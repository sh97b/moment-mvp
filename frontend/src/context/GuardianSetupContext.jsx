import { createContext, useContext, useState } from 'react'

const GuardianSetupContext = createContext(null)

const initialSetup = {
  personName: '',
  homeLocation: '합성 기준 위치 A',
  homePosition: null,
  places: ['늘봄 경로당', '햇살공원'],
  returnTime: '18:00',
  lifePattern: '화요일과 목요일 오후 2시쯤 늘봄복지관에 방문하고, 평일에는 오전 산책을 자주 합니다. 대부분 오후 6시 전에 귀가합니다.',
}

export function GuardianSetupProvider({ children }) {
  const [setup, setSetup] = useState(initialSetup)

  const updateField = (field, value) => {
    setSetup((current) => ({ ...current, [field]: value }))
  }

  return (
    <GuardianSetupContext.Provider value={{ setup, updateField }}>
      {children}
    </GuardianSetupContext.Provider>
  )
}

export function useGuardianSetup() {
  const context = useContext(GuardianSetupContext)

  if (!context) {
    throw new Error('useGuardianSetup은 GuardianSetupProvider 안에서 사용해야 합니다.')
  }

  return context
}
