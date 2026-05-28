import { ConfigProvider } from 'antd'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthScreen } from '@/components/auth-screen'
import { APP_ROUTES } from '@/constants/routes'
import { AppAuthProvider, useAppAuth } from '@/context/AppAuthContext'
import CoreEntryPage from '@/pages/core-entry-page'
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
