import { useCallback } from 'react'
import { ConfigProvider } from 'antd'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthScreen } from '@/components/auth-screen'
import { APP_ROUTES } from '@/constants/routes'
import { AppAuthProvider, useAppAuth } from '@/context/AppAuthContext'
import CoreEntryPage from '@/pages/core-entry-page'
import { XIAOCAI_CHAT_ANTD_THEME } from '@/theme/chatTheme'

function AppRoutes() {
  const {
    authError,
    authParams,
    authStage,
    authenticate,
    hasAccessToken,
    mockAuthEnabled,
    mockUsers,
    selectedMockUser,
    setSelectedMockUserId,
  } = useAppAuth()
  const handleSubmitMock = useCallback((userId: string) => {
    void authenticate('mock', userId)
  }, [authenticate])
  const handleRetry = useCallback(() => {
    void authenticate()
  }, [authenticate])

  if (!hasAccessToken) {
    return (
      <AuthScreen
        authError={authError}
        authMode={authParams.mode}
        authStage={authStage}
        mockAuthEnabled={mockAuthEnabled}
        mockUsers={mockUsers}
        onRetry={handleRetry}
        onSelectMockUser={setSelectedMockUserId}
        onSubmitMock={handleSubmitMock}
        selectedMockUser={selectedMockUser}
      />
    )
  }

  return (
    <Routes>
      <Route path={APP_ROUTES.chat} element={<CoreEntryPage />} />
      <Route path="*" element={<CoreEntryPage />} />
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
