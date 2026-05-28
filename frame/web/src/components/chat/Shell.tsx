import type { ReactNode } from 'react'

type ShellProps = {
  workspace: ReactNode
}

export function Shell({ workspace }: ShellProps) {
  return (
    <div className="xiaocai-chat-page" style={{ background: '#f6f8fc', height: '100%', minHeight: 0 }}>
      {workspace}
    </div>
  )
}
