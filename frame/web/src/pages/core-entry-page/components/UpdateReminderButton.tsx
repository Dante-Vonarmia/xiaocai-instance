import { useState } from 'react'
import type { FlarePackageStatus } from '@/services/api'
import { useFlareUpdateStatus } from '../hooks/useFlareUpdateStatus'

function versionText(item: FlarePackageStatus) {
  const current = item.current || '?'
  const latest = item.latest || '?'
  return `${item.registry}:${item.package} ${current} → ${latest}`
}

function visiblePackages(packages: FlarePackageStatus[]) {
  const updates = packages.filter((item) => item.update_available)
  if (updates.length > 0) {
    return updates
  }
  return packages.slice(0, 4)
}

export function UpdateReminderButton() {
  const [open, setOpen] = useState(false)
  const status = useFlareUpdateStatus()
  const packages = visiblePackages(status.packages)

  return (
    <div className="core-entry-update-reminder">
      <button
        aria-label={status.title}
        className={`core-entry-update-button is-${status.tone}`}
        onClick={() => setOpen((value) => !value)}
        title={status.title}
        type="button"
      >
        <span className="core-entry-update-dot" />
        <span className="core-entry-update-text">
          {status.updateCount > 0 ? '更新' : '已对齐'}
        </span>
      </button>
      {open ? (
        <div className="core-entry-update-popover" role="status">
          <div className="core-entry-update-popover-title">{status.title}</div>
          {status.error ? (
            <div className="core-entry-update-popover-error">{status.error}</div>
          ) : null}
          {status.runtimeGate ? (
            <div className="core-entry-update-popover-line">
              Runtime gate：{status.runtimeGate.passed ? '通过' : '异常'}
            </div>
          ) : null}
          <div className="core-entry-update-package-list">
            {packages.map((item) => (
              <div className="core-entry-update-package" key={`${item.registry}:${item.package}`}>
                {versionText(item)}
              </div>
            ))}
          </div>
          <button
            className="core-entry-update-refresh"
            disabled={status.loadState === 'checking'}
            onClick={status.refresh}
            type="button"
          >
            {status.loadState === 'checking' ? '检查中…' : '重新检查'}
          </button>
        </div>
      ) : null}
    </div>
  )
}
