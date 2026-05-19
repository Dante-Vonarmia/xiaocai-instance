const IOS_WEBKIT_UA_PATTERN = /iP(hone|od|ad)/i
const KEYBOARD_OPEN_THRESHOLD_PX = 120
const RESYNC_DELAYS_MS = [120, 260, 420]

/**
 * 同步 iOS Safari 真机可视区高度到 CSS 变量。
 * 不能依赖静态 vh/svh，否则地址栏与键盘变化时会错位。
 */
export function setupIosViewportHeightSync(): void {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    return
  }

  const userAgent = window.navigator.userAgent || ''
  if (!IOS_WEBKIT_UA_PATTERN.test(userAgent)) {
    return
  }

  const rootStyle = document.documentElement.style
  const rootClassList = document.documentElement.classList
  let resyncTimerIds: number[] = []

  const clearResyncTimers = () => {
    resyncTimerIds.forEach((id) => window.clearTimeout(id))
    resyncTimerIds = []
  }

  const isEditableTarget = (target: Element | null): boolean => {
    if (!(target instanceof HTMLElement)) {
      return false
    }

    const tagName = target.tagName.toLowerCase()
    if (tagName === 'textarea') {
      return true
    }

    if (tagName === 'input') {
      const inputType = (target as HTMLInputElement).type
      return inputType !== 'button' && inputType !== 'submit' && inputType !== 'reset'
    }

    return target.isContentEditable
  }

  const syncViewportHeight = () => {
    const visualViewport = window.visualViewport
    const visualViewportHeight = visualViewport?.height ?? window.innerHeight
    const visualViewportTop = visualViewport?.offsetTop ?? 0
    const nextHeight = Math.round(visualViewportHeight + visualViewportTop)
    const keyboardOffset = Math.max(
      0,
      Math.round(window.innerHeight - visualViewportHeight - visualViewportTop),
    )
    const hasFocusedEditable = isEditableTarget(document.activeElement)
    const isKeyboardOpen = hasFocusedEditable && keyboardOffset > KEYBOARD_OPEN_THRESHOLD_PX

    rootStyle.setProperty('--xiaocai-app-viewport-height', `${nextHeight}px`)
    rootStyle.setProperty('--xiaocai-viewport-keyboard-offset', `${keyboardOffset}px`)

    if (isKeyboardOpen) {
      rootClassList.add('xiaocai-ios-keyboard-open')
      return
    }

    rootClassList.remove('xiaocai-ios-keyboard-open')
  }

  const scheduleResync = () => {
    clearResyncTimers()
    syncViewportHeight()
    resyncTimerIds = RESYNC_DELAYS_MS.map((delayMs) => window.setTimeout(() => {
      syncViewportHeight()
    }, delayMs))
  }

  syncViewportHeight()

  window.addEventListener('resize', syncViewportHeight, { passive: true })
  window.addEventListener('orientationchange', scheduleResync, { passive: true })
  window.addEventListener('focusin', scheduleResync, { passive: true })
  window.addEventListener('focusout', scheduleResync, { passive: true })
  window.addEventListener('pageshow', scheduleResync, { passive: true })
  document.addEventListener('visibilitychange', scheduleResync, { passive: true })
  window.visualViewport?.addEventListener('resize', syncViewportHeight, { passive: true })
  window.visualViewport?.addEventListener('scroll', scheduleResync, { passive: true })
}
