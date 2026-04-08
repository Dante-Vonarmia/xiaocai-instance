type LogoutHeaderProps = {
  onLogout?: () => void
}

function LogoutHeader({ onLogout }: LogoutHeaderProps) {
  if (!onLogout) {
    return null
  }

  return (
    <header
      style={{
        alignItems: 'center',
        background: '#ffffff',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'flex-end',
        padding: '8px 12px',
      }}
    >
      <button
        onClick={onLogout}
        style={{
          background: '#ffffff',
          border: '1px solid #d1d5db',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '14px',
          padding: '6px 12px',
        }}
        type="button"
      >
        退出
      </button>
    </header>
  )
}

export default LogoutHeader
