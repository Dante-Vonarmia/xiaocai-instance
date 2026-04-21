export const APP_ROUTES = {
  chat: '/',
  settingsRoot: '/settings',
  settingsProfile: '/settings/profile',
  settingsSystem: '/settings/system',
} as const

export type SettingsSection = 'profile' | 'system'
