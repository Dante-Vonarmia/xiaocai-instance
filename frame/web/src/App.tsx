import { ConfigProvider } from 'antd'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthScreen } from '@/components/auth-screen'
import { APP_ROUTES } from '@/constants/routes'
import { AppAuthProvider, useAppAuth } from '@/context/AppAuthContext'
import CoreEntryPage from '@/pages/core-entry-page'
import ProfilePage from '@/pages/ProfilePage'
import SettingsPage from '@/pages/SettingsPage'
import { XIAOCAI_CHAT_ANTD_THEME } from '@/theme/chatTheme'

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
      <Route path={APP_ROUTES.profile} element={<ProfilePage onLogout={logout} />} />
      <Route path={APP_ROUTES.settingsProfile} element={<Navigate to={APP_ROUTES.profile} replace />} />
      <Route path={APP_ROUTES.settingsRoot} element={<Navigate to={APP_ROUTES.settingsSystem} replace />} />
      <Route path={APP_ROUTES.settingsSystem} element={<SettingsPage onLogout={logout} />} />
      <Route path="*" element={<CoreEntryPage onLogout={logout} />} />
    </Routes>
  )
}

function App() {
  return (
    <ConfigProvider theme={XIAOCAI_CHAT_ANTD_THEME}>
      <AppAuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AppAuthProvider>
    </ConfigProvider>
  )
}

export default App
