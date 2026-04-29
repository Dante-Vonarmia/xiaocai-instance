import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthScreen } from '@/components/auth-screen'
import { APP_ROUTES } from '@/constants/routes'
import { AppAuthProvider, useAppAuth } from '@/context/AppAuthContext'
import CoreEntryPage from '@/pages/core-entry-page'
import SettingsPage from '@/pages/SettingsPage'

function AppRoutes() {
  const {
    hasAccessToken,
    authParams,
    authStage,
    authError,
    mockUsers,
    selectedMockUser,
    setSelectedMockUserId,
    authenticate,
    logout,
  } = useAppAuth()

  if (!hasAccessToken) {
    return (
      <AuthScreen
        authError={authError}
        authMode={authParams.mode}
        authStage={authStage}
        mockUsers={mockUsers}
        onRetry={() => void authenticate()}
        onSelectMockUser={setSelectedMockUserId}
        onSubmitMock={(userId) => void authenticate('mock', userId)}
        selectedMockUser={selectedMockUser}
      />
    )
  }

  return (
    <Routes>
      <Route path={APP_ROUTES.chat} element={<CoreEntryPage onLogout={logout} />} />
      <Route path={APP_ROUTES.settingsRoot} element={<Navigate to={APP_ROUTES.settingsProfile} replace />} />
      <Route path={`${APP_ROUTES.settingsRoot}/:section`} element={<SettingsPage onLogout={logout} />} />
      <Route path="*" element={<CoreEntryPage onLogout={logout} />} />
    </Routes>
  )
}

function App() {
  return (
    <AppAuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppAuthProvider>
  )
}

export default App
