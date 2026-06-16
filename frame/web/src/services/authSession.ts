const CURRENT_USER_DISPLAY_NAME_KEY = 'current_user_display_name'

function canUseBrowserStorage() {
  return typeof window !== 'undefined' && typeof window.sessionStorage !== 'undefined'
}

export function getCurrentUserDisplayName() {
  if (!canUseBrowserStorage()) {
    return ''
  }

  try {
    return window.sessionStorage.getItem(CURRENT_USER_DISPLAY_NAME_KEY) || ''
  } catch {
    return ''
  }
}

export function setCurrentUserDisplayName(displayName: string) {
  if (!canUseBrowserStorage()) {
    return
  }

  window.sessionStorage.setItem(CURRENT_USER_DISPLAY_NAME_KEY, displayName.trim())
}

export function clearCurrentUserDisplayName() {
  if (!canUseBrowserStorage()) {
    return
  }

  window.sessionStorage.removeItem(CURRENT_USER_DISPLAY_NAME_KEY)
}
