const CURRENT_USER_DISPLAY_NAME_KEY = 'current_user_display_name'

function canUseBrowserStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function getCurrentUserDisplayName() {
  if (!canUseBrowserStorage()) {
    return ''
  }

  try {
    return window.localStorage.getItem(CURRENT_USER_DISPLAY_NAME_KEY) || ''
  } catch {
    return ''
  }
}

export function setCurrentUserDisplayName(displayName: string) {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.setItem(CURRENT_USER_DISPLAY_NAME_KEY, displayName.trim())
}

export function clearCurrentUserDisplayName() {
  if (!canUseBrowserStorage()) {
    return
  }

  window.localStorage.removeItem(CURRENT_USER_DISPLAY_NAME_KEY)
}
